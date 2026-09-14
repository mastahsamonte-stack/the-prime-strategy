#!/usr/bin/env python3
"""
Commercial Underwriter - deterministic model (Solutions layer).

Claude does the research and the narrative; this script does the arithmetic so the
waterfall, capital stack, debt sizing, returns, and sensitivity grids are identical every run.

Usage:
  python3 underwrite.py example <class>            print a sample deal JSON
                        (multifamily | retail | nnn | office | industrial | mixed | storage | sizing)
  python3 underwrite.py model deal.json [--out model.json] [--tables tables.html]
  python3 underwrite.py size sizing.json [--out sizing.json] [--tables tables.html]
  python3 underwrite.py selftest

No third-party dependencies. All money in annual USD unless a key says otherwise.
"""
import argparse
import copy
import json
import math
import sys

# --------------------------------------------------------------------------- helpers

def pmt(rate, amort_years, principal, interest_only=False):
    """Annual debt service."""
    if principal <= 0:
        return 0.0
    if interest_only or not amort_years:
        return principal * rate
    r = rate / 12.0
    n = amort_years * 12
    if r == 0:
        return principal / amort_years
    m = principal * r / (1 - (1 + r) ** (-n))
    return m * 12


def balance_after(rate, amort_years, principal, years, interest_only=False):
    if principal <= 0:
        return 0.0
    if interest_only or not amort_years:
        return principal
    r = rate / 12.0
    n = amort_years * 12
    k = min(years * 12, n)
    if r == 0:
        return principal * (1 - k / n)
    m = principal * r / (1 - (1 + r) ** (-n))
    return principal * (1 + r) ** k - m * ((1 + r) ** k - 1) / r


def irr(cashflows, lo=-0.99, hi=10.0):
    """Bisection IRR. cashflows[0] is the equity outlay (negative)."""
    def npv(rate):
        return sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))
    if all(cf <= 0 for cf in cashflows) or all(cf >= 0 for cf in cashflows):
        return None
    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = npv(mid)
        if abs(f_mid) < 1e-7:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def expiry_year(expiry, start_year):
    """'2029-06' -> proforma year index (1-based) in which the lease rolls; None = no expiry."""
    if not expiry:
        return None
    try:
        y = int(str(expiry)[:4])
    except ValueError:
        return None
    return max(1, y - start_year + 1)


# --------------------------------------------------------------------------- normalize spaces

def normalize_spaces(deal):
    """Return a list of spaces with annual in-place and market rent, sf, occupied, lease_type, roll_year."""
    inc = deal.get("income", {})
    prop = deal.get("property", {})
    start_year = int(deal.get("analysis_year", 2026))
    spaces = []
    for s in inc.get("spaces", []) or []:
        sf = float(s.get("sf", 0) or 0)
        basis = s.get("basis", "psf_year")
        mult = 12.0 if basis == "psf_month" else 1.0
        inplace = float(s.get("rent_psf", 0) or 0) * sf * mult
        market = float(s.get("market_rent_psf", 0) or 0) * sf * mult
        spaces.append({
            "tenant": s.get("tenant", ""), "sf": sf, "count": 1,
            "occupied": bool(s.get("occupied", inplace > 0)),
            "inplace": inplace, "market": market,
            "lease_type": (s.get("lease_type") or "NNN").upper(),
            "roll_year": expiry_year(s.get("expiry"), start_year),
            "recovers": s.get("recovers"), "aggregate": bool(s.get("aggregate", False)),
        })
    for u in inc.get("units", []) or []:
        count = int(u.get("count", 0) or 0)
        occ = int(u.get("occupied", count) if u.get("occupied") is not None else count)
        rent = float(u.get("rent", 0) or 0) * 12
        market = float(u.get("market_rent", u.get("rent", 0)) or 0) * 12
        sf = float(u.get("sf", 0) or 0)
        if occ:
            spaces.append({"tenant": f"{u.get('type','unit')} x{occ} (occupied)", "sf": sf * occ, "count": occ,
                           "occupied": True, "inplace": rent * occ, "market": market * occ,
                           "lease_type": "GROSS", "roll_year": 2, "recovers": None, "aggregate": True})
        if count - occ:
            v = count - occ
            spaces.append({"tenant": f"{u.get('type','unit')} x{v} (vacant)", "sf": sf * v, "count": v,
                           "occupied": False, "inplace": 0.0, "market": market * v,
                           "lease_type": "GROSS", "roll_year": None, "recovers": None, "aggregate": True})
    total_sf = float(prop.get("rentable_sf") or sum(s["sf"] for s in spaces) or 0)
    total_units = prop.get("units") or (sum(s["count"] for s in spaces) if inc.get("units") else None)
    return spaces, total_sf, total_units


# --------------------------------------------------------------------------- expenses

RECOVERABLE_DEFAULT = ["taxes", "insurance", "cam", "utilities"]
EXPENSE_KEYS = ["taxes", "insurance", "utilities", "repairs_maintenance", "cam", "admin", "payroll", "marketing", "other"]


def base_expenses(deal, price):
    ex = deal.get("expenses", {})
    out = {}
    t = ex.get("taxes", 0)
    if isinstance(t, dict):
        ra = t.get("reassess")
        if ra:
            out["taxes"] = price * float(ra.get("assessment_ratio", 1.0)) * float(ra.get("mill_rate", 0))
        else:
            out["taxes"] = float(t.get("amount", 0) or 0)
    else:
        out["taxes"] = float(t or 0)
    for k in EXPENSE_KEYS[1:]:
        v = ex.get(k, 0)
        out[k] = float(v or 0)
    return out


def reserves_amount(deal, total_sf, total_units):
    ex = deal.get("expenses", {})
    if ex.get("reserves_per_unit") and total_units:
        return float(ex["reserves_per_unit"]) * float(total_units)
    return float(ex.get("reserves_psf", 0) or 0) * total_sf


# --------------------------------------------------------------------------- cases

CASE_DEFAULTS = {
    "conservative": {"vacancy_delta": 0.0, "mark_to_market": False, "vacant_lease_pct": 0.90,
                     "vacant_start_year": 2, "inplace_growth": 0.02, "credit_loss_delta": 0.0},
    "base":         {"vacancy_delta": 0.0, "mark_to_market": True, "vacant_lease_pct": 1.0,
                     "vacant_start_year": 1, "inplace_growth": None, "credit_loss_delta": 0.0},
    "upside":       {"vacancy_delta": -0.02, "mark_to_market": True, "vacant_lease_pct": 1.0,
                     "vacant_start_year": 1, "inplace_growth": None, "credit_loss_delta": -0.005},
}


def case_params(deal, name):
    p = dict(CASE_DEFAULTS[name])
    p.update((deal.get("cases") or {}).get(name, {}) or {})
    return p


def income_for_year(deal, spaces, case, year, total_sf):
    """Return dict with gpr, vacancy, credit_loss, recoveries, other, egi, occupied_share for a year."""
    inc = deal.get("income", {})
    growth = deal.get("growth", {})
    g_rent = float(growth.get("rent", 0.03))
    g_inplace = case["inplace_growth"] if case["inplace_growth"] is not None else g_rent
    lease_up_months = float(deal.get("capital", {}).get("lease_up_months", 6) or 0)
    vac_rate = max(0.0, float(inc.get("vacancy_rate", 0.07)) + case["vacancy_delta"])
    cl_rate = max(0.0, float(inc.get("credit_loss_rate", 0.01)) + case["credit_loss_delta"])

    gpr = 0.0
    occupied_sf = 0.0
    nnn_occupied_sf = 0.0
    for s in spaces:
        mkt = s["market"] * (1 + g_rent) ** (year - 1)
        if s["occupied"]:
            rolled = case["mark_to_market"] and s["roll_year"] is not None and year >= s["roll_year"]
            rent = mkt if rolled else s["inplace"] * (1 + g_inplace) ** (year - 1)
            gpr += rent
            occupied_sf += s["sf"]
            if s["lease_type"] in ("NNN", "NN", "MG"):
                nnn_occupied_sf += s["sf"]
        else:
            start = case["vacant_start_year"]
            if year < start:
                continue
            rent = mkt * case["vacant_lease_pct"]
            if year == start and start == 1:
                rent *= max(0.0, (12 - lease_up_months) / 12.0)
            gpr += rent
            occupied_sf += s["sf"]
            if s["lease_type"] in ("NNN", "NN", "MG"):
                nnn_occupied_sf += s["sf"]
    vacancy = gpr * vac_rate
    credit = gpr * cl_rate
    occ_share = (occupied_sf / total_sf) if total_sf else 1.0
    return {"gpr": gpr, "vacancy": vacancy, "credit_loss": credit, "occupied_share": occ_share,
            "nnn_share": (nnn_occupied_sf / total_sf) if total_sf else 0.0,
            "other": float(inc.get("other_income_annual", 0) or 0) * (1 + g_rent) ** (year - 1)}


def run_case(deal, name, price, spaces, total_sf, total_units, years):
    case = case_params(deal, name)
    inc = deal.get("income", {})
    growth = deal.get("growth", {})
    g_exp = float(growth.get("expense", 0.03))
    keys = inc.get("recoverable_expense_keys", RECOVERABLE_DEFAULT)
    eff = float(inc.get("recovery_efficiency", 0.9))
    mgmt_pct = float(deal.get("expenses", {}).get("management_pct", 0.05) or 0)
    reserves0 = reserves_amount(deal, total_sf, total_units)
    ex0 = base_expenses(deal, price)
    rows = []
    for y in range(1, years + 2):  # one extra year for exit NOI
        i = income_for_year(deal, spaces, case, y, total_sf)
        ex = {k: v * (1 + g_exp) ** (y - 1) for k, v in ex0.items()}
        recoverable = sum(ex.get(k, 0) for k in keys)
        recoveries = recoverable * i["nnn_share"] * eff * (1 - float(inc.get("vacancy_rate", 0.07)))
        gpi = i["gpr"] + recoveries + i["other"]
        egi = gpi - i["vacancy"] - i["credit_loss"]
        mgmt = egi * mgmt_pct
        opex = sum(ex.values()) + mgmt
        reserves = reserves0 * (1 + g_exp) ** (y - 1)
        noi = egi - opex - reserves
        rows.append({"year": y, "gpr": i["gpr"], "recoveries": recoveries, "other": i["other"], "gpi": gpi,
                     "vacancy": i["vacancy"], "credit_loss": i["credit_loss"], "egi": egi,
                     "expenses": ex, "management": mgmt, "opex": opex, "reserves": reserves, "noi": noi,
                     "occupied_share": i["occupied_share"]})
    return {"name": name, "params": case, "years": rows}


# --------------------------------------------------------------------------- debt + capital

def size_debt(deal, price, noi_y1_conservative):
    fin = deal.get("financing", {})
    first = fin.get("first", {}) or {}
    ltv = float(first.get("ltv", 0.70))
    rate = float(first.get("rate", 0.07))
    amort = first.get("amort_years", 25)
    io = bool(first.get("interest_only", False))
    second = fin.get("second") or {}
    loan2 = 0.0
    ads2 = 0.0
    if second:
        loan2 = float(second.get("amount") or price * float(second.get("pct_of_price", 0) or 0))
        ads2 = pmt(float(second.get("rate", 0.06)), second.get("amort_years"), loan2, bool(second.get("interest_only", True)))
    ltv_loan = price * ltv
    loan = ltv_loan
    dscr_loan = None
    if first.get("size_by_dscr", True) and first.get("dscr_floor"):
        # lenders size on COMBINED coverage: the second position's payment comes off what the first may carry
        max_ads = noi_y1_conservative / float(first["dscr_floor"]) - ads2
        const = pmt(rate, amort, 1.0, io)
        dscr_loan = max_ads / const if const > 0 else ltv_loan
        loan = min(ltv_loan, max(0.0, dscr_loan))
    if first.get("amount"):
        loan = float(first["amount"])
    ads1 = pmt(rate, amort, loan, io)
    return {"first": {"type": first.get("type", "bank"), "amount": loan, "ltv_loan": ltv_loan, "dscr_loan": dscr_loan,
                      "rate": rate, "amort_years": amort, "term_years": first.get("term_years", 5),
                      "interest_only": io, "ads": ads1, "constant": (ads1 / loan) if loan else 0.0},
            "second": {"type": second.get("type"), "amount": loan2, "rate": float(second.get("rate", 0)) if second else 0.0,
                       "interest_only": bool(second.get("interest_only", True)) if second else True,
                       "amort_years": second.get("amort_years") if second else None, "ads": ads2},
            "total_debt": loan + loan2, "total_ads": ads1 + ads2}


def capital_stack(deal, price, debt, spaces, cons_y1, total_sf, total_units):
    cap = deal.get("capital", {})
    closing = price * float(cap.get("closing_cost_pct", 0.03))
    vacant_sf = sum(s["sf"] for s in spaces if not s["occupied"])
    vacant_market_rent = sum(s["market"] for s in spaces if not s["occupied"])
    ti = vacant_sf * float(cap.get("ti_psf_vacant", 0) or 0)
    if cap.get("ti_per_unit_vacant") and total_units:
        ti = sum(s["count"] for s in spaces if not s["occupied"]) * float(cap["ti_per_unit_vacant"])
    lc = vacant_market_rent * float(cap.get("lc_pct", 0.05)) * float(cap.get("lc_years", 5))
    capex = float(cap.get("capex", 0) or 0)
    monthly_burden = (cons_y1["opex"] + cons_y1["reserves"] + debt["total_ads"]) / 12.0
    shortfall_m = max(0.0, (debt["total_ads"] - cons_y1["noi"]) / 12.0)
    carry = shortfall_m * float(cap.get("lease_up_months", 6) or 0)
    reserve = monthly_burden * float(cap.get("reserve_months", 6) or 0)
    fee_pct = float(cap.get("acq_fee_pct", 0.0747))
    uses_before_fee = price + closing + ti + lc + capex + carry + reserve
    raise_ = (uses_before_fee - debt["total_debt"]) / (1 - fee_pct) if fee_pct < 1 else uses_before_fee - debt["total_debt"]
    fee = raise_ * fee_pct
    uses = {"purchase_price": price, "closing_costs": closing, "ti": ti, "leasing_commissions": lc, "capex": capex,
            "lease_up_carry": carry, "operating_reserve": reserve, "acquisition_fee": fee}
    total_uses = sum(uses.values())
    sources = {"first_debt": debt["first"]["amount"], "second_debt": debt["second"]["amount"], "equity_raise": raise_}
    return {"uses": uses, "total_uses": total_uses, "sources": sources, "total_sources": sum(sources.values()),
            "down_payment": price - debt["total_debt"], "equity_ex_down_payment": raise_ - (price - debt["total_debt"]),
            "reconciles": abs(total_uses - sum(sources.values())) < 1.0, "vacant_sf": vacant_sf}


# --------------------------------------------------------------------------- full model

def rollover_schedule(spaces, years=5):
    total = sum(s["inplace"] for s in spaces if s["occupied"]) or 1.0
    sched = {}
    for s in spaces:
        if s["occupied"] and s["roll_year"]:
            y = min(s["roll_year"], years + 1)
            sched[y] = sched.get(y, 0.0) + s["inplace"]
    return {f"year_{y}": sched.get(y, 0.0) / total for y in range(1, years + 2)}


def walt(spaces, start_year=2026):
    num = den = 0.0
    for s in spaces:
        if s["occupied"] and s["inplace"] > 0:
            rem = (s["roll_year"] - 0.5) if s["roll_year"] else 10.0
            num += rem * s["inplace"]
            den += s["inplace"]
    return (num / den) if den else 0.0


def model(deal, price=None):
    price = float(price if price is not None else deal["price"])
    spaces, total_sf, total_units = normalize_spaces(deal)
    growth = deal.get("growth", {})
    hold = int(growth.get("hold_years", 5))
    hurdles = {"coc_go": 0.08, "dscr_go": 1.25, "debt_yield_go": 0.08, "dscr_nogo": 1.10, "coc_conditional": 0.06}
    hurdles.update(deal.get("hurdles", {}) or {})

    cases = {n: run_case(deal, n, price, spaces, total_sf, total_units, hold) for n in ("conservative", "base", "upside")}
    cons1 = cases["conservative"]["years"][0]
    debt = size_debt(deal, price, cons1["noi"])
    stack = capital_stack(deal, price, debt, spaces, cons1, total_sf, total_units)
    equity = stack["sources"]["equity_raise"]
    going_in_cap = cons1["noi"] / price if price else 0.0
    exit_cap = growth.get("exit_cap") or (going_in_cap + float(growth.get("exit_cap_spread", 0.005)))
    exit_cap = max(exit_cap, going_in_cap)  # never lower than entry
    sale_cost = float(growth.get("sale_cost_pct", 0.03))

    results = {}
    for n, c in cases.items():
        rows = c["years"]
        flows = [-equity]
        pro = []
        for y in range(1, hold + 1):
            r = rows[y - 1]
            ads = debt["total_ads"]
            cfbt = r["noi"] - ads
            capital_items = 0.0
            if y == 1:
                capital_items = 0.0  # TI/LC/capex are funded in the raise, not year-1 cash flow
            pro.append({"year": y, "gpi": r["gpi"], "egi": r["egi"], "opex": r["opex"], "reserves": r["reserves"],
                        "noi": r["noi"], "ads": ads, "cfbt": cfbt, "occupied_share": r["occupied_share"],
                        "dscr": (r["noi"] / ads) if ads else None})
            flows.append(cfbt)
        exit_noi = rows[hold]["noi"]
        gross_sale = exit_noi / exit_cap if exit_cap else 0.0
        bal1 = balance_after(debt["first"]["rate"], debt["first"]["amort_years"], debt["first"]["amount"], hold, debt["first"]["interest_only"])
        bal2 = balance_after(debt["second"]["rate"], debt["second"]["amort_years"], debt["second"]["amount"], hold, debt["second"]["interest_only"]) if debt["second"]["amount"] else 0.0
        net_sale = gross_sale * (1 - sale_cost) - bal1 - bal2
        flows[-1] += net_sale
        y1 = pro[0]
        breakeven = ((y1["opex"] + y1["reserves"] + y1["ads"]) / rows[0]["gpi"]) if rows[0]["gpi"] else None
        results[n] = {
            "proforma": pro, "exit": {"exit_cap": exit_cap, "exit_noi": exit_noi, "gross_sale": gross_sale,
                                      "loan_balance": bal1 + bal2, "net_sale_proceeds": net_sale},
            "metrics": {"noi_y1": y1["noi"], "cap_rate": (y1["noi"] / price) if price else 0.0,
                        "dscr": y1["dscr"], "debt_yield": (y1["noi"] / debt["total_debt"]) if debt["total_debt"] else None,
                        "coc": (y1["cfbt"] / equity) if equity else None, "break_even_occupancy": breakeven,
                        "equity_multiple": (sum(flows[1:]) / equity) if equity else None,
                        "irr": irr(flows), "loan_constant": debt["first"]["constant"],
                        "negative_leverage": (y1["noi"] / price) < debt["first"]["constant"] if price and debt["first"]["amount"] else False},
            "cash_flows": flows,
        }

    m = results["conservative"]["metrics"]
    flags = []
    roll = rollover_schedule(spaces, hold)
    term = int(debt["first"].get("term_years") or hold)
    heavy_roll = [k for k, v in roll.items() if v > 0.30 and int(k.split("_")[1]) <= term]
    if heavy_roll and float(deal.get("capital", {}).get("reserve_months", 6) or 0) == 0:
        flags.append(f"Rollover > 30% of GPR inside loan term ({', '.join(heavy_roll)}) with no lease-up reserve")
    if m["negative_leverage"]:
        flags.append("Negative leverage: going-in cap below loan constant")
    if m["dscr"] is not None and m["dscr"] < hurdles["dscr_go"]:
        flags.append(f"Conservative DSCR {m['dscr']:.2f} below {hurdles['dscr_go']:.2f}")
    if m["debt_yield"] is not None and m["debt_yield"] < hurdles["debt_yield_go"]:
        flags.append(f"Debt yield {m['debt_yield']*100:.1f}% below {hurdles['debt_yield_go']*100:.0f}%")
    if m["coc"] is not None and m["coc"] < hurdles["coc_go"]:
        flags.append(f"Conservative cash-on-cash {m['coc']*100:.1f}% below {hurdles['coc_go']*100:.0f}% hurdle")
    if not stack["reconciles"]:
        flags.append("Sources do not equal uses")
    top = sorted((s for s in spaces if s["occupied"] and not s.get("aggregate")), key=lambda s: -s["inplace"])
    gpr_in = sum(s["inplace"] for s in top) or 1.0
    concentration = {"top1": (top[0]["inplace"] / gpr_in) if top else 0.0,
                     "top3": (sum(s["inplace"] for s in top[:3]) / gpr_in) if top else 0.0}
    if concentration["top1"] > 0.40:
        flags.append(f"Single tenant is {concentration['top1']*100:.0f}% of in-place rent; underwrite the guarantor")

    verdict = "CONDITIONAL"
    if m["dscr"] is not None and m["dscr"] < hurdles["dscr_nogo"]:
        verdict = "NO-GO"
    elif m["negative_leverage"] and (m["coc"] or 0) <= 0 and stack["vacant_sf"] == 0 \
            and not any(s["market"] > s["inplace"] * 1.05 for s in spaces if s["occupied"]):
        verdict = "NO-GO"  # negative leverage, negative cash flow, and no value-add path
    elif (m["dscr"] or 0) >= hurdles["dscr_go"] and (m["debt_yield"] or 0) >= hurdles["debt_yield_go"] \
            and (m["coc"] or 0) >= hurdles["coc_go"] and not heavy_roll:
        verdict = "GO"
    mtm = sum(s["market"] - s["inplace"] for s in spaces if s["occupied"])

    return {
        "inputs": {"price": price, "rentable_sf": total_sf, "units": total_units, "hold_years": hold,
                   "price_psf": (price / total_sf) if total_sf else None,
                   "price_per_unit": (price / total_units) if total_units else None},
        "lease": {"spaces": spaces, "walt_years": walt(spaces), "rollover_pct_of_gpr": roll,
                  "mark_to_market_gap": mtm, "concentration": concentration,
                  "physical_occupancy": (sum(s["sf"] for s in spaces if s["occupied"]) / total_sf) if total_sf else None},
        "cases": {n: {"params": cases[n]["params"], "waterfall_y1": cases[n]["years"][0]} for n in cases},
        "debt": debt, "capital_stack": stack, "results": results,
        "verdict_script": verdict, "flags": flags, "hurdles": hurdles,
        "note": "Verdict is the script's math-only read on the Conservative case. Claude caps it at CONDITIONAL if any verdict-driving figure is red (needs more data).",
    }


def sensitivities(deal, base_out):
    price = base_out["inputs"]["price"]
    fin = copy.deepcopy(deal)
    fin["financing"]["first"]["size_by_dscr"] = False
    fin["financing"]["first"]["amount"] = base_out["debt"]["first"]["amount"]
    rate0 = base_out["debt"]["first"]["rate"]
    vac0 = float(deal.get("income", {}).get("vacancy_rate", 0.07))
    grid_rate_vac = []
    for dr in (-0.01, -0.005, 0.0, 0.005, 0.01):
        row = []
        for dv in (-0.03, 0.0, 0.03, 0.06):
            d = copy.deepcopy(fin)
            d["financing"]["first"]["rate"] = rate0 + dr
            d["income"]["vacancy_rate"] = max(0.0, vac0 + dv)
            o = model(d, price)
            row.append(o["results"]["conservative"]["metrics"]["dscr"])
        grid_rate_vac.append({"rate": rate0 + dr, "dscr_by_vacancy": row})
    cap0 = base_out["results"]["conservative"]["exit"]["exit_cap"]
    noi0 = base_out["results"]["conservative"]["exit"]["exit_noi"]
    grid_noi_cap = []
    for dn in (-0.10, -0.05, 0.0, 0.05, 0.10):
        row = []
        for dc in (-0.005, 0.0, 0.005, 0.01):
            v = noi0 * (1 + dn) / (cap0 + dc)
            row.append(v)
        grid_noi_cap.append({"noi_delta": dn, "value_by_exit_cap": row})
    grid_price = []
    for dp in (-0.10, -0.05, 0.0, 0.05):
        o = model(deal, price * (1 + dp))
        mm = o["results"]["conservative"]["metrics"]
        grid_price.append({"price": price * (1 + dp), "coc": mm["coc"], "dscr": mm["dscr"], "cap_rate": mm["cap_rate"],
                           "equity_raise": o["capital_stack"]["sources"]["equity_raise"], "verdict": o["verdict_script"]})
    return {"rate_x_vacancy_dscr": {"vacancy_cols": [max(0.0, vac0 + dv) for dv in (-0.03, 0.0, 0.03, 0.06)], "rows": grid_rate_vac},
            "noi_x_exit_cap_value": {"exit_cap_cols": [cap0 + dc for dc in (-0.005, 0.0, 0.005, 0.01)], "rows": grid_noi_cap},
            "price_grid": grid_price}


# --------------------------------------------------------------------------- sizing (MARKET mode)

def size_market(cfg):
    basis = cfg.get("rent_basis", "psf_year")
    rent = float(cfg["market_rent"])
    vac = float(cfg.get("vacancy_rate", 0.08))
    cl = float(cfg.get("credit_loss_rate", 0.01))
    er = float(cfg.get("expense_ratio", 0.35))
    rec = float(cfg.get("recovery_ratio", 0.0)) if (cfg.get("lease_type", "NNN").upper() in ("NNN", "NN", "MG")) else 0.0
    cap = float(cfg["cap_rate"])
    fin = cfg.get("financing", {}).get("first", {})
    capc = cfg.get("capital", {})
    rows = []
    for size in cfg["sizes"]:
        gpr = rent * size * (12 if basis == "unit_month" else 1)
        egi = gpr * (1 - vac - cl)
        opex = egi * er
        recov = opex * rec * (1 - vac)
        reserves = (float(cfg.get("reserves_per_unit", 300)) * size) if basis == "unit_month" else float(cfg.get("reserves_psf", 0.25)) * size
        noi = egi + recov - opex - reserves
        price = noi / cap if cap else 0.0
        ltv = float(fin.get("ltv", 0.70)); r = float(fin.get("rate", 0.07)); am = fin.get("amort_years", 25); io = bool(fin.get("interest_only", False))
        loan = price * ltv
        if fin.get("dscr_floor"):
            const = pmt(r, am, 1.0, io)
            loan = min(loan, (noi / float(fin["dscr_floor"])) / const)
        ads = pmt(r, am, loan, io)
        closing = price * float(capc.get("closing_cost_pct", 0.03))
        vacant_units = size * vac
        ti = vacant_units * float(capc.get("ti_per_unit_vacant", 0) if basis == "unit_month" else capc.get("ti_psf_vacant", 0) or 0)
        lc = gpr * vac * float(capc.get("lc_pct", 0.05)) * float(capc.get("lc_years", 5))
        capex = size * float(capc.get("capex_per_unit", 3000) if basis == "unit_month" else capc.get("capex_psf", 5))
        reserve = (opex + reserves + ads) / 12 * float(capc.get("reserve_months", 6))
        fee_pct = float(capc.get("acq_fee_pct", 0.0747))
        raise_ = (price + closing + ti + lc + capex + reserve - loan) / (1 - fee_pct)
        fee = raise_ * fee_pct
        cfbt = noi - ads
        rows.append({"size": size, "gpr": gpr, "egi": egi, "opex": opex + reserves, "recoveries": recov, "noi": noi,
                     "price": price, "price_per": (price / size) if size else None, "loan": loan, "ads": ads,
                     "dscr": (noi / ads) if ads else None, "closing": closing, "ti_lc": ti + lc, "capex": capex,
                     "reserve": reserve, "acquisition_fee": fee, "equity_needed": raise_,
                     "down_payment": price - loan, "coc": (cfbt / raise_) if raise_ else None,
                     "debt_yield": (noi / loan) if loan else None})
    return {"market": cfg.get("market"), "asset_class": cfg.get("asset_class"), "rent_basis": basis,
            "assumptions": {k: cfg.get(k) for k in ("market_rent", "lease_type", "vacancy_rate", "credit_loss_rate",
                                                    "expense_ratio", "recovery_ratio", "cap_rate")},
            "sizes": rows,
            "note": "capex placeholder and any unverified assumption must be labeled [ASSUMPTION] in the report"}


# --------------------------------------------------------------------------- HTML tables

def _m(v):
    if v is None:
        return "—"
    s = "${:,.0f}".format(abs(v))
    return f'<span class="neg">({s})</span>' if v < 0 else s


def _p(v, d=1):
    return "—" if v is None else f"{v*100:.{d}f}%"


def _x(v):
    return "—" if v is None else f"{v:.2f}x"


def _dscr(v, floor=1.25):
    if v is None:
        return "—"
    s = f"{v:.2f}"
    return f'<span class="neg">{s}</span>' if v < floor else s


def tables_html(out, sens):
    h = []
    r = out["results"]
    ms = {n: r[n]["metrics"] for n in r}
    h.append("<h3>Returns summary (Year 1)</h3><table><tr><th class='l'>Metric</th><th>Conservative</th><th>Base</th><th>Upside</th></tr>")
    for label, key, fmt in (("NOI", "noi_y1", _m), ("Going-in cap rate", "cap_rate", _p), ("DSCR", "dscr", _dscr),
                            ("Debt yield", "debt_yield", _p), ("Cash-on-cash", "coc", _p),
                            ("Break-even occupancy", "break_even_occupancy", _p), ("Equity multiple (hold)", "equity_multiple", _x),
                            ("Levered IRR (projected)", "irr", _p)):
        h.append(f"<tr><td class='l'>{label}</td>" + "".join(f"<td>{fmt(ms[n][key])}</td>" for n in ("conservative", "base", "upside")) + "</tr>")
    h.append("</table><p class='note'>Projected, targeted, not guaranteed. Verdict judged on the Conservative case.</p>")

    h.append("<h3>Year 1 waterfall</h3><table><tr><th class='l'>Line</th><th>Conservative</th><th>Base</th><th>Upside</th></tr>")
    w = {n: out["cases"][n]["waterfall_y1"] for n in out["cases"]}
    for label, key in (("Gross potential rent", "gpr"), ("Recovery income", "recoveries"), ("Other income", "other"),
                       ("Gross potential income", "gpi"), ("Less vacancy", "vacancy"), ("Less credit loss", "credit_loss"),
                       ("Effective gross income", "egi"), ("Operating expenses (incl. mgmt)", "opex"), ("Replacement reserves", "reserves"),
                       ("Net operating income", "noi")):
        h.append(f"<tr><td class='l'>{label}</td>" + "".join(f"<td>{_m(w[n][key])}</td>" for n in ("conservative", "base", "upside")) + "</tr>")
    h.append("</table>")

    ex = w["conservative"]["expenses"]
    h.append("<h3>Expense budget (Year 1, Conservative)</h3><table><tr><th class='l'>Line</th><th>Annual</th></tr>")
    for k, v in ex.items():
        if v:
            h.append(f"<tr><td class='l'>{k.replace('_', ' ').title()}</td><td>{_m(v)}</td></tr>")
    h.append(f"<tr><td class='l'>Management</td><td>{_m(w['conservative']['management'])}</td></tr>")
    h.append(f"<tr><td class='l'>Replacement reserves</td><td>{_m(w['conservative']['reserves'])}</td></tr>")
    h.append(f"<tr><td class='l'><b>Total OpEx + reserves</b></td><td><b>{_m(w['conservative']['opex'] + w['conservative']['reserves'])}</b></td></tr></table>")

    pro = r["conservative"]["proforma"]
    h.append("<h3>5-year proforma (Conservative)</h3><table><tr><th class='l'>Line</th>" + "".join(f"<th>Year {p['year']}</th>" for p in pro) + "</tr>")
    for label, key, fmt in (("GPI", "gpi", _m), ("EGI", "egi", _m), ("OpEx + reserves", None, None), ("NOI", "noi", _m),
                            ("Debt service", "ads", _m), ("Cash flow before tax", "cfbt", _m), ("DSCR", "dscr", _dscr)):
        if key is None:
            h.append(f"<tr><td class='l'>{label}</td>" + "".join(f"<td>{_m(p['opex'] + p['reserves'])}</td>" for p in pro) + "</tr>")
        else:
            h.append(f"<tr><td class='l'>{label}</td>" + "".join(f"<td>{fmt(p[key])}</td>" for p in pro) + "</tr>")
    e = r["conservative"]["exit"]
    h.append(f"</table><p class='note'>Exit: Year {len(pro)+1} NOI {_m(e['exit_noi'])} at {_p(e['exit_cap'], 2)} exit cap = {_m(e['gross_sale'])} gross; "
             f"net of sale costs and loan payoff {_m(e['loan_balance'])} = {_m(e['net_sale_proceeds'])} to equity (projected).</p>")

    cs = out["capital_stack"]
    h.append("<h3>Sources &amp; uses</h3><table><tr><th class='l'>Uses</th><th>Amount</th><th class='l'>Sources</th><th>Amount</th></tr>")
    u = list(cs["uses"].items()); s = list(cs["sources"].items())
    for i in range(max(len(u), len(s))):
        ul = f"<td class='l'>{u[i][0].replace('_', ' ').title()}</td><td>{_m(u[i][1])}</td>" if i < len(u) else "<td></td><td></td>"
        sl = f"<td class='l'>{s[i][0].replace('_', ' ').title()}</td><td>{_m(s[i][1])}</td>" if i < len(s) else "<td></td><td></td>"
        h.append(f"<tr>{ul}{sl}</tr>")
    ok = "pass" if cs["reconciles"] else "fail"
    h.append(f"<tr><td class='l'><b>Total uses</b></td><td><b>{_m(cs['total_uses'])}</b></td><td class='l'><b>Total sources</b></td><td><b>{_m(cs['total_sources'])}</b> <span class='{ok}'>{'reconciles' if cs['reconciles'] else 'DOES NOT RECONCILE'}</span></td></tr></table>")
    h.append(f"<p class='note'>Cash to close (equity raise) {_m(cs['sources']['equity_raise'])}: down payment {_m(cs['down_payment'])} + closing, TI/LC, capex, carry, reserves and acquisition fee {_m(cs['equity_ex_down_payment'])}.</p>")

    d = out["debt"]
    h.append("<h3>Debt</h3><table><tr><th class='l'>Position</th><th>Amount</th><th>Rate</th><th>Amort</th><th>Term</th><th>Annual debt service</th><th>Constant</th></tr>")
    f = d["first"]
    h.append(f"<tr><td class='l'>First — {f['type']}{' (IO)' if f['interest_only'] else ''}</td><td>{_m(f['amount'])}</td><td>{_p(f['rate'], 2)}</td><td>{f['amort_years'] or '—'}</td><td>{f['term_years']}</td><td>{_m(f['ads'])}</td><td>{_p(f['constant'], 2)}</td></tr>")
    if d["second"]["amount"]:
        sd = d["second"]
        h.append(f"<tr><td class='l'>Second — {sd['type']}{' (IO)' if sd['interest_only'] else ''}</td><td>{_m(sd['amount'])}</td><td>{_p(sd['rate'], 2)}</td><td>{sd['amort_years'] or '—'}</td><td></td><td>{_m(sd['ads'])}</td><td></td></tr>")
    h.append("</table>")
    if f["dscr_loan"] is not None:
        h.append(f"<p class='note'>LTV-sized loan {_m(f['ltv_loan'])} vs DSCR-sized loan {_m(f['dscr_loan'])}; the lesser governs.</p>")

    lease = out["lease"]
    h.append("<h3>Lease abstract</h3><table><tr><th class='l'>Tenant</th><th>SF</th><th>In-place rent</th><th>Market rent</th><th>Type</th><th>Rolls (yr)</th></tr>")
    for sp in lease["spaces"]:
        h.append(f"<tr><td class='l'>{sp['tenant'] or ('VACANT' if not sp['occupied'] else '')}</td><td>{sp['sf']:,.0f}</td><td>{_m(sp['inplace'])}</td><td>{_m(sp['market'])}</td><td>{sp['lease_type']}</td><td>{sp['roll_year'] or '—'}</td></tr>")
    h.append("</table>")
    roll = lease["rollover_pct_of_gpr"]
    h.append(f"<p class='note'>Physical occupancy {_p(lease['physical_occupancy'])}; WALT {lease['walt_years']:.1f} yrs; mark-to-market gap {_m(lease['mark_to_market_gap'])}/yr; "
             f"top tenant {_p(lease['concentration']['top1'], 0)} of rent. Rollover by year: " + ", ".join(f"Y{k.split('_')[1]} {_p(v, 0)}" for k, v in roll.items()) + ".</p>")

    if sens:
        g = sens["rate_x_vacancy_dscr"]
        h.append("<h3>Sensitivity: DSCR by rate × vacancy (Conservative, Year 1)</h3><table><tr><th class='l'>Rate \\ Vacancy</th>" + "".join(f"<th>{_p(v, 0)}</th>" for v in g["vacancy_cols"]) + "</tr>")
        for row in g["rows"]:
            h.append(f"<tr><td class='l'>{_p(row['rate'], 2)}</td>" + "".join(f"<td>{_dscr(v)}</td>" for v in row["dscr_by_vacancy"]) + "</tr>")
        h.append("</table>")
        g = sens["noi_x_exit_cap_value"]
        h.append("<h3>Sensitivity: exit value by NOI × exit cap</h3><table><tr><th class='l'>NOI \\ Exit cap</th>" + "".join(f"<th>{_p(c, 2)}</th>" for c in g["exit_cap_cols"]) + "</tr>")
        for row in g["rows"]:
            h.append(f"<tr><td class='l'>{row['noi_delta']*100:+.0f}%</td>" + "".join(f"<td>{_m(v)}</td>" for v in row["value_by_exit_cap"]) + "</tr>")
        h.append("</table>")
        h.append("<h3>Sensitivity: purchase price</h3><table><tr><th>Price</th><th>Cap rate</th><th>DSCR</th><th>Cash-on-cash</th><th>Equity needed</th><th>Script read</th></tr>")
        for row in sens["price_grid"]:
            h.append(f"<tr><td>{_m(row['price'])}</td><td>{_p(row['cap_rate'])}</td><td>{_dscr(row['dscr'])}</td><td>{_p(row['coc'])}</td><td>{_m(row['equity_raise'])}</td><td>{row['verdict']}</td></tr>")
        h.append("</table>")
    if out["flags"]:
        h.append("<div class='warn-box'><b>Script flags:</b><ul>" + "".join(f"<li>{x}</li>" for x in out["flags"]) + "</ul></div>")
    return "\n".join(h)


def sizing_tables_html(res):
    unit = "units" if res["rent_basis"] == "unit_month" else "SF"
    h = [f"<h3>Market sizing — {res.get('asset_class','')} in {res.get('market','')}</h3>",
         "<table><tr><th>Size</th><th>GPR</th><th>NOI</th><th>Price @ cap</th><th>Price per " + ("unit" if unit == "units" else "SF") + "</th><th>Loan</th><th>DSCR</th><th>Down payment</th><th>Acq. fee</th><th>Equity needed</th><th>Cash-on-cash</th></tr>"]
    for r in res["sizes"]:
        h.append(f"<tr><td>{r['size']:,.0f} {unit}</td><td>{_m(r['gpr'])}</td><td>{_m(r['noi'])}</td><td>{_m(r['price'])}</td><td>{_m(r['price_per'])}</td><td>{_m(r['loan'])}</td><td>{_dscr(r['dscr'])}</td><td>{_m(r['down_payment'])}</td><td>{_m(r['acquisition_fee'])}</td><td><b>{_m(r['equity_needed'])}</b></td><td>{_p(r['coc'])}</td></tr>")
    a = res["assumptions"]
    h.append("</table><p class='note'>Assumptions: rent " + str(a.get("market_rent")) + f" ({res['rent_basis']}), {a.get('lease_type')}, vacancy {_p(a.get('vacancy_rate'))}, expense ratio {_p(a.get('expense_ratio'))}, cap {_p(a.get('cap_rate'), 2)}. Equity needed includes closing, TI/LC, capex placeholder [ASSUMPTION], reserves, and the acquisition fee.</p>")
    return "\n".join(h)


# --------------------------------------------------------------------------- examples

def example(kind):
    fin = {"first": {"type": "bank", "ltv": 0.70, "rate": 0.0725, "amort_years": 25, "term_years": 5,
                     "interest_only": False, "dscr_floor": 1.25, "size_by_dscr": True}}
    cap = {"closing_cost_pct": 0.03, "ti_psf_vacant": 15, "lc_pct": 0.05, "lc_years": 5, "capex": 40000,
           "lease_up_months": 6, "reserve_months": 6, "acq_fee_pct": 0.0747}
    growth = {"rent": 0.03, "expense": 0.03, "hold_years": 5, "exit_cap": None, "exit_cap_spread": 0.005, "sale_cost_pct": 0.03}
    base = {"analysis_year": 2026, "property": {"name": "", "address": "", "city": "", "state": "", "asset_class": kind,
                                                "rentable_sf": None, "units": None, "year_built": None},
            "price": 0, "income": {}, "expenses": {}, "financing": fin, "capital": cap, "growth": growth,
            "hurdles": {"coc_go": 0.08, "dscr_go": 1.25, "debt_yield_go": 0.08, "dscr_nogo": 1.10},
            "_notes": "Every figure here is a placeholder; replace with verified values and cite them. Taxes: use reassess {assessment_ratio, mill_rate} so the bill is at purchase price."}
    if kind == "sizing":
        return {"market": "City, ST", "asset_class": "retail", "rent_basis": "psf_year", "market_rent": 16.0, "lease_type": "NNN",
                "vacancy_rate": 0.08, "credit_loss_rate": 0.01, "expense_ratio": 0.30, "recovery_ratio": 0.70, "cap_rate": 0.075,
                "reserves_psf": 0.25, "sizes": [6000, 12000, 25000], "financing": fin,
                "capital": {"closing_cost_pct": 0.03, "ti_psf_vacant": 15, "lc_pct": 0.05, "lc_years": 5, "capex_psf": 5,
                            "reserve_months": 6, "acq_fee_pct": 0.0747},
                "_notes": "For multifamily use rent_basis unit_month, market_rent = avg rent/unit/mo, sizes = unit counts, reserves_per_unit, capex_per_unit, ti_per_unit_vacant."}
    if kind == "multifamily":
        base["property"].update({"rentable_sf": 10800, "units": 12, "year_built": 1965})
        base["price"] = 1450000
        base["income"] = {"units": [{"type": "1BR", "count": 4, "occupied": 4, "rent": 1350, "market_rent": 1450, "sf": 700},
                                    {"type": "2BR", "count": 8, "occupied": 7, "rent": 1600, "market_rent": 1750, "sf": 1000}],
                          "other_income_annual": 4800, "vacancy_rate": 0.05, "credit_loss_rate": 0.01}
        base["expenses"] = {"taxes": {"reassess": {"assessment_ratio": 1.0, "mill_rate": 0.0135}}, "insurance": 14000, "utilities": 18000,
                            "repairs_maintenance": 12000, "cam": 6000, "management_pct": 0.05, "admin": 3000, "marketing": 1500,
                            "reserves_per_unit": 300}
        base["capital"].update({"ti_psf_vacant": 0, "ti_per_unit_vacant": 4000, "capex": 60000})
        base["financing"]["first"].update({"type": "agency-small-balance", "ltv": 0.75, "amort_years": 30, "dscr_floor": 1.25})
    elif kind == "retail":
        base["property"].update({"rentable_sf": 12000, "year_built": 1988})
        base["price"] = 1350000
        base["income"] = {"spaces": [{"tenant": "Dollar General", "sf": 9000, "rent_psf": 11.5, "market_rent_psf": 13.0, "lease_type": "NNN", "expiry": "2029-06", "occupied": True},
                                     {"tenant": "Nail salon", "sf": 1500, "rent_psf": 16.0, "market_rent_psf": 16.0, "lease_type": "NNN", "expiry": "2027-12", "occupied": True},
                                     {"tenant": "VACANT", "sf": 1500, "rent_psf": 0, "market_rent_psf": 16.0, "lease_type": "NNN", "occupied": False}],
                          "other_income_annual": 0, "vacancy_rate": 0.08, "credit_loss_rate": 0.01,
                          "recoverable_expense_keys": ["taxes", "insurance", "cam"], "recovery_efficiency": 0.9}
        base["expenses"] = {"taxes": {"reassess": {"assessment_ratio": 1.0, "mill_rate": 0.012}}, "insurance": 9000, "utilities": 3000,
                            "repairs_maintenance": 8000, "cam": 14000, "management_pct": 0.04, "admin": 3000, "marketing": 500, "reserves_psf": 0.25}
        base["financing"]["second"] = {"type": "seller_carry", "pct_of_price": 0.15, "rate": 0.06, "interest_only": True, "term_years": 5}
    elif kind == "nnn":
        base["property"].update({"rentable_sf": 9100, "year_built": 2012})
        base["price"] = 1330000
        base["income"] = {"spaces": [{"tenant": "Dollar Tree (corporate)", "sf": 9100, "rent_psf": 12.0, "market_rent_psf": 12.5, "lease_type": "NNN", "expiry": "2032-01", "occupied": True}],
                          "vacancy_rate": 0.03, "credit_loss_rate": 0.0, "recoverable_expense_keys": ["taxes", "insurance", "cam"], "recovery_efficiency": 1.0}
        base["expenses"] = {"taxes": {"reassess": {"assessment_ratio": 1.0, "mill_rate": 0.011}}, "insurance": 5000, "cam": 4000, "management_pct": 0.02, "admin": 1500, "reserves_psf": 0.15}
        base["capital"].update({"capex": 10000, "reserve_months": 3})
    elif kind == "office":
        base["property"].update({"rentable_sf": 20000, "year_built": 1985})
        base["price"] = 1400000
        base["income"] = {"spaces": [{"tenant": "Law firm", "sf": 6000, "rent_psf": 18.0, "market_rent_psf": 17.0, "lease_type": "GROSS", "expiry": "2028-03", "occupied": True},
                                     {"tenant": "Insurance agency", "sf": 4000, "rent_psf": 17.0, "market_rent_psf": 17.0, "lease_type": "GROSS", "expiry": "2027-06", "occupied": True},
                                     {"tenant": "Dental", "sf": 3000, "rent_psf": 20.0, "market_rent_psf": 19.0, "lease_type": "GROSS", "expiry": "2031-01", "occupied": True},
                                     {"tenant": "VACANT", "sf": 7000, "rent_psf": 0, "market_rent_psf": 17.0, "lease_type": "GROSS", "occupied": False}],
                          "vacancy_rate": 0.12, "credit_loss_rate": 0.01}
        base["expenses"] = {"taxes": {"reassess": {"assessment_ratio": 1.0, "mill_rate": 0.014}}, "insurance": 12000, "utilities": 42000,
                            "repairs_maintenance": 22000, "cam": 26000, "management_pct": 0.04, "admin": 6000, "marketing": 2000, "reserves_psf": 0.30}
        base["capital"].update({"ti_psf_vacant": 25, "capex": 120000, "lease_up_months": 12})
        base["financing"]["first"].update({"amort_years": 20, "dscr_floor": 1.30})
    elif kind == "industrial":
        base["property"].update({"rentable_sf": 25000, "year_built": 1998})
        base["price"] = 2000000
        base["income"] = {"spaces": [{"tenant": "HVAC contractor", "sf": 15000, "rent_psf": 8.5, "market_rent_psf": 9.5, "lease_type": "NNN", "expiry": "2029-09", "occupied": True},
                                     {"tenant": "Cabinet shop", "sf": 10000, "rent_psf": 8.0, "market_rent_psf": 9.5, "lease_type": "NNN", "expiry": "2027-04", "occupied": True}],
                          "vacancy_rate": 0.05, "credit_loss_rate": 0.01, "recoverable_expense_keys": ["taxes", "insurance", "cam"], "recovery_efficiency": 0.95}
        base["expenses"] = {"taxes": {"reassess": {"assessment_ratio": 1.0, "mill_rate": 0.0115}}, "insurance": 11000, "utilities": 2000,
                            "repairs_maintenance": 9000, "cam": 12000, "management_pct": 0.03, "admin": 3000, "reserves_psf": 0.20}
        base["capital"].update({"ti_psf_vacant": 5, "capex": 50000})
    elif kind == "mixed":
        base["property"].update({"rentable_sf": 9000, "units": 6, "year_built": 1920})
        base["price"] = 1150000
        base["income"] = {"spaces": [{"tenant": "Cafe", "sf": 1800, "rent_psf": 22.0, "market_rent_psf": 22.0, "lease_type": "MG", "expiry": "2028-08", "occupied": True},
                                     {"tenant": "Barber", "sf": 1200, "rent_psf": 20.0, "market_rent_psf": 21.0, "lease_type": "MG", "expiry": "2027-02", "occupied": True}],
                          "units": [{"type": "1BR", "count": 6, "occupied": 6, "rent": 1300, "market_rent": 1400, "sf": 1000}],
                          "other_income_annual": 2400, "vacancy_rate": 0.06, "credit_loss_rate": 0.01,
                          "recoverable_expense_keys": ["taxes"], "recovery_efficiency": 0.8}
        base["expenses"] = {"taxes": {"reassess": {"assessment_ratio": 1.0, "mill_rate": 0.013}}, "insurance": 10000, "utilities": 14000,
                            "repairs_maintenance": 9000, "cam": 4000, "management_pct": 0.05, "admin": 2500, "reserves_psf": 0.30}
        base["capital"].update({"capex": 45000})
    elif kind == "storage":
        base["property"].update({"rentable_sf": 45000, "units": 400, "year_built": 2005})
        base["price"] = 3300000
        base["income"] = {"spaces": [{"tenant": "Occupied units (blended)", "sf": 38000, "rent_psf": 1.05, "market_rent_psf": 1.15, "basis": "psf_month", "lease_type": "GROSS", "expiry": "2026-12", "occupied": True, "aggregate": True},
                                     {"tenant": "Vacant units", "sf": 7000, "rent_psf": 0, "market_rent_psf": 1.15, "basis": "psf_month", "lease_type": "GROSS", "occupied": False}],
                          "other_income_annual": 18000, "vacancy_rate": 0.10, "credit_loss_rate": 0.02}
        base["expenses"] = {"taxes": {"reassess": {"assessment_ratio": 1.0, "mill_rate": 0.012}}, "insurance": 12000, "utilities": 9000,
                            "repairs_maintenance": 15000, "cam": 6000, "management_pct": 0.06, "admin": 8000, "payroll": 48000, "marketing": 9000, "reserves_psf": 0.15}
        base["capital"].update({"ti_psf_vacant": 0, "capex": 40000, "lease_up_months": 3})
    else:
        raise SystemExit(f"unknown example kind: {kind}")
    return base


# --------------------------------------------------------------------------- selftest

def selftest():
    # pmt sanity: $1,000,000 at 7.25% / 25 yr ≈ $7,228/mo
    assert abs(pmt(0.0725, 25, 1_000_000) / 12 - 7228) < 5, pmt(0.0725, 25, 1_000_000) / 12
    assert abs(pmt(0.06, None, 500_000, True) - 30_000) < 0.01
    assert abs(balance_after(0.0725, 25, 1_000_000, 25) - 0) < 1
    assert abs(irr([-100, 0, 0, 0, 0, 200]) - (2 ** 0.2 - 1)) < 1e-6
    for k in ("multifamily", "retail", "nnn", "office", "industrial", "mixed", "storage"):
        out = model(example(k))
        assert out["capital_stack"]["reconciles"], k
        assert out["results"]["conservative"]["metrics"]["noi_y1"] != 0, k
        fee = out["capital_stack"]["uses"]["acquisition_fee"]
        raise_ = out["capital_stack"]["sources"]["equity_raise"]
        assert abs(fee / raise_ - 0.0747) < 1e-9, k
        sens = sensitivities(example(k), out)
        assert len(sens["price_grid"]) == 4
        tables_html(out, sens)
    res = size_market(example("sizing"))
    assert len(res["sizes"]) == 3 and all(r["equity_needed"] > 0 for r in res["sizes"])
    sizing_tables_html(res)
    print("selftest: OK")


# --------------------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("example"); e.add_argument("kind")
    m = sub.add_parser("model"); m.add_argument("deal"); m.add_argument("--out"); m.add_argument("--tables"); m.add_argument("--no-sens", action="store_true")
    s = sub.add_parser("size"); s.add_argument("config"); s.add_argument("--out"); s.add_argument("--tables")
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "example":
        print(json.dumps(example(a.kind), indent=2))
    elif a.cmd == "selftest":
        selftest()
    elif a.cmd == "model":
        deal = json.load(open(a.deal))
        out = model(deal)
        sens = None if a.no_sens else sensitivities(deal, out)
        out["sensitivities"] = sens
        if a.out:
            json.dump(out, open(a.out, "w"), indent=2, default=str)
        if a.tables:
            open(a.tables, "w").write(tables_html(out, sens))
        mm = out["results"]["conservative"]["metrics"]
        cs = out["capital_stack"]
        print(f"verdict(script): {out['verdict_script']}")
        print(f"price {out['inputs']['price']:,.0f} | NOI(cons) {mm['noi_y1']:,.0f} | cap {mm['cap_rate']*100:.2f}% | DSCR {mm['dscr']:.2f} | "
              f"debt yield {(mm['debt_yield'] or 0)*100:.1f}% | CoC {(mm['coc'] or 0)*100:.1f}% | IRR {(mm['irr'] or 0)*100:.1f}% | EM {(mm['equity_multiple'] or 0):.2f}x")
        print(f"equity needed {cs['sources']['equity_raise']:,.0f} (down payment {cs['down_payment']:,.0f} + other {cs['equity_ex_down_payment']:,.0f}; acq fee {cs['uses']['acquisition_fee']:,.0f})")
        for f in out["flags"]:
            print(f"flag: {f}")
    elif a.cmd == "size":
        res = size_market(json.load(open(a.config)))
        if a.out:
            json.dump(res, open(a.out, "w"), indent=2)
        if a.tables:
            open(a.tables, "w").write(sizing_tables_html(res))
        for r in res["sizes"]:
            print(f"{r['size']:>8,.0f}: price {r['price']:,.0f} | NOI {r['noi']:,.0f} | loan {r['loan']:,.0f} | DSCR {r['dscr']:.2f} | equity needed {r['equity_needed']:,.0f} | CoC {(r['coc'] or 0)*100:.1f}%")


if __name__ == "__main__":
    main()
