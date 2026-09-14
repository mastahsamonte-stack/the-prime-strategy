# Report Structure — Commercial Underwriting HTML

One self-contained HTML file, inline CSS, PATH Report Design System palette (below, verbatim).
Filename: `Commercial_Underwriting_<Street-or-City>_v1.0_<YYYY-MM-DD>.html` saved to `~/Cowork/`
root. Actor everywhere: **P.A.T.H. Operation**. Never overwrite a prior version.

## CSS (paste verbatim)
```css
:root{--ink:#1F2A37;--blue:#1E6FBA;--line:#d7dde3;--soft:#f4f6f8;--good:#1a7f37;--bad:#cf222e;}
*{box-sizing:border-box;}
body{font-family:Arial,Helvetica,sans-serif;color:var(--ink);font-size:12px;line-height:1.5;margin:0;padding:0;}
.wrap{max-width:980px;margin:0 auto;padding:0 32px 40px;}
.report-header{background:#0D1B2A;color:#fff;padding:26px 32px;}
.report-header h1{color:#fff;font-size:24px;margin:0 0 6px;}
.report-header .addr{color:#9fb3c8;font-size:13px;margin:2px 0;}
.report-header .byline{color:#7d93a8;font-size:11px;margin-top:10px;}
.vstamp{display:inline-block;background:#1E6FBA;color:#fff;font-size:11px;padding:3px 10px;border-radius:4px;margin-top:10px;letter-spacing:.5px;}
.reason-for-update{background:#fffbeb;border-left:4px solid #f59e0b;padding:10px 14px;margin-bottom:16px;font-size:13px;}
.verdict-band{padding:14px 32px;color:#fff;font-size:16px;font-weight:bold;}
/* Verdict band bg: GO=#1a7f37 | CONDITIONAL=#9a6700 | NO-GO=#cf222e */
h1{color:var(--blue);font-size:24px;margin:0 0 4px;}
h2{color:var(--blue);font-size:15px;border-bottom:2px solid var(--blue);padding-bottom:4px;margin:26px 0 10px;}
h3{color:var(--blue);font-size:13px;margin:18px 0 8px;}
.chip{display:inline-block;color:#fff;font-weight:bold;padding:4px 12px;border-radius:4px;font-size:12px;}
.banner{background:var(--soft);border-left:4px solid var(--blue);padding:10px 14px;margin:14px 0;font-size:11px;}
.warn-box{background:#fff8ed;border-left:4px solid #f59e0b;padding:10px 14px;margin:14px 0;font-size:11px;}
table{border-collapse:collapse;width:100%;margin:8px 0 4px;font-size:11px;}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:right;}
th{background:var(--blue);color:#fff;}
td.l,th.l{text-align:left;}
tr:nth-child(even) td{background:var(--soft);}
.pass{color:var(--good);font-weight:bold;} .fail{color:var(--bad);font-weight:bold;}
.neg{color:var(--bad);} .verified{color:var(--good);} .flagged{color:#9a6700;}
.note{font-size:11px;color:#5b6770;font-style:italic;margin:4px 0 0;}
.foot{margin-top:30px;border-top:1px solid var(--line);padding-top:10px;font-size:10px;color:#5b6770;}
.acronym-index{background:#f0f4f8;border-left:4px solid var(--blue);padding:16px 20px;margin-top:32px;font-size:14px;}
.acronym-index h3{margin-top:0;color:#0D1B2A;}
.acronym-index dl{margin:8px 0;display:grid;grid-template-columns:130px 1fr;gap:10px;}
.acronym-index dt{font-weight:600;color:#0D1B2A;}
```

## Header block
Dark header: title "Commercial Underwriting — <Property or Market>", address line, class + mode
(DEAL / MARKET), byline "Prepared for P.A.T.H. Operation · <date>", version stamp chip
`v1.0 · YYYY-MM-DD`. On v1.1+ add the `.reason-for-update` block directly under the header.
Then the verdict band: GO / CONDITIONAL / NO-GO + one-line hook (e.g., "Pencils at $2.1M with
seller carry; ask of $2.4M does not.").

## The 16 sections (in this order)
1. **Verdict & Headline Numbers** — verdict, price (or price at three sizes), Conservative NOI, going-in
   cap vs market cap, DSCR, CoC, total equity needed incl. acquisition fee, the single condition if CONDITIONAL.
2. **Property / Market Snapshot** — class, mode, SF or units, year built, lot, zoning, occupancy, WALT,
   price/SF or price/unit, condition flags (ground truth marked ✓).
3. **Market Overview** — submarket rents, vacancy, absorption, new supply, demand drivers, comps table
   (each comp with source + date), replacement-cost check.
4. **Rent Roll & Lease Analysis** — lease abstract table, WALT, rollover schedule, mark-to-market gap,
   tenant concentration, lease red flags. MARKET mode: representative rent roll for three sizes.
5. **Revenue Analysis** — GPR, recoveries, other income, vacancy, credit loss, EGI for Conservative /
   Base / Upside.
6. **Expense Budget** — line items with source and ✓/⚠/🔴, reassessed taxes, expense ratio vs band.
7. **Proforma (5-Year)** — NOI, ADS, CFBT, capital items, sale in year 5 (exit cap = entry + 50 bps),
   Conservative case with Base and Upside summarized.
8. **Capital Stack & Acquisition Fee** — sources & uses, acquisition fee line (~7.47% of raise),
   DSCR-constrained loan vs LTV loan, cash to close split (down payment / everything else).
9. **Financing & Debt Service** — structure(s) modeled, rate, amort, term, DSCR, debt yield, loan
   constant vs cap (negative-leverage flag), balloon date, refi/exit plan, SBA 504 flag if owner-occupant.
10. **OPTION A: Equity JV Partner** — cap table, P.A.T.H. fees, 5-year return illustration (targeted, not guaranteed).
11. **OPTION B: Private Money Lender** — terms, LTV, DSCR, exit plan.
12. **Recommended Path** — which option, at what price, with which condition, and why.
13. **Sensitivity** — the three grids from `underwriting-model.md`.
14. **Diligence Checklist & Who To Call** — 15–25 items from `capital-needs.md` + contacts with numbers.
15. **Risk Register** — 5–8 risks (rollover, single tenant, tax reassessment, rate reset at balloon,
    capex, environmental, market supply, regulatory) with severity + mitigation.
15.5 **Fact-Check Summary** — figures checked / ✓ / ⚠ / 🔴, governing sources, ruling status,
    confirmation that the full ladder including the deep-dive rung ran on every ⚠/🔴.
15.6 **Cash-Flow Optimization — Levers & Upside** — MANDATORY final content section before the
    index, per `~/Cowork/skills/optimize-cash-flow/SKILL.md` (mark-to-market, expense recoveries,
    billboard/cell/parking income, utility bill-back, tax abatement appeal, refinance at stabilization).
16. **Acronym Index + Footer** — alphabetical, every acronym in the report (ADS, CAM, CFBT, CoC,
    DSCR, EGI, GBA, GPI, GPR, IO, IRR, LC, LTC, LTV, MG, MOB, NNN, NOI, NRSF, OM, OpEx, PCA, PM,
    RSF, SBA, SNDA, T-12, TI, USF, WALT, and any others used). Footer: "For discussion purposes
    only — not legal, tax, or financial advice." + date.

## Rendering conventions
- ✓ green (`.verified`) verified; ⚠ amber (`.flagged`) conflicting / unverified, conservative value
  in the math, "pending ruling"; 🔴 needs more data, `[ASSUMPTION — pending verification]`, verdict
  capped at CONDITIONAL. Each material figure carries its source (name + date) inline or footnoted.
- Negative values and DSCR < 1.25 in `.neg`. Never round DSCR up.
- Tables come from `scripts/underwrite.py --tables`; embed them, then write the narrative around them.
- Investor-safe words only: targeted, projected, potential, not guaranteed.
