# Underwriting Model — Definitions, Lender Conventions, Hurdles

The script (`scripts/underwrite.py`) does the arithmetic. This file defines every line so the
narrative and the numbers agree, and sets the P.A.T.H. hurdles the verdict uses.

## The waterfall (annual)
```
Gross Potential Rent (GPR)          all space at underwriting rent (vacant at market)
+ Recovery income                   NNN/MG reimbursements (see rent-and-lease-analysis §2)
+ Other income                      parking, signage, laundry, storage, late fees, cell tower
= Gross Potential Income (GPI)
− Vacancy                           % of GPR (physical)
− Credit loss                       % of GPR (non-payment, concessions)
= Effective Gross Income (EGI)
− Operating expenses                real estate taxes (REASSESSED), insurance, utilities (landlord
                                    share), repairs & maintenance, CAM/landscaping/snow, management,
                                    admin/legal/accounting, payroll (if any), marketing
− Replacement reserves              $/SF or $/unit per year (lender-required; not "optional")
= Net Operating Income (NOI)
− Annual debt service (ADS)         first + any second position
= Cash flow before tax (CFBT)
− Capital items (TI/LC, capex)      in the year incurred (proforma only)
= Net cash flow
```

**Tax reassessment rule:** most jurisdictions reassess on sale (CA Prop 13 explicitly; MA, TX, FL,
AZ, NV effectively on next cycle). Model taxes as `purchase price × assessment ratio × mill rate`
for THIS county, not the seller's current bill. The seller's bill is ⚠ by definition.

**Management fee:** 4–6% of EGI for multifamily/retail, 3–5% office/industrial, minimum $300–
$500/unit/yr multifamily. Model it even if P.A.T.H. Operation self-manages (a lender will).

**Replacement reserves:** multifamily $250–$350/unit/yr; commercial $0.15–$0.30/SF/yr; more for
older roofs/HVAC. Lenders underwrite them; so do we.

## How the script builds the three cases (defaults; override under `cases` in the deal JSON)
| Case | Occupied space | Vacant space | Vacancy factor | In-place growth |
|---|---|---|---|---|
| Conservative | in-place rent, no mark-to-market on expiry | vacant all of Year 1 (carry), leases at 90% of market from Year 2 | verified rate on leased space (vacant space is excluded on top of that) | 2%/yr (contractual-only; below the 3% expense growth so margins compress) |
| Base | marked to market on expiry | leases at market in Year 1 after `lease_up_months` | verified rate | market rent growth (3% default) |
| Upside | marked to market on expiry | leases at market in Year 1 after `lease_up_months` | verified rate − 2 pts | market rent growth |

Debt is sized once, on the Conservative Year 1 NOI, as the lesser of LTV × price and the
DSCR-constrained loan (combined coverage: a seller-carry second's payment comes off what the
first may carry). The same loan is then held across all three cases so the cases differ only in
operations, not in leverage.

## Returns and ratios
| Metric | Formula | P.A.T.H. read |
|---|---|---|
| Cap rate (going-in) | NOI Year 1 ÷ purchase price | compare to verified market cap; buying above market cap = margin |
| Price per SF / per unit | price ÷ RSF or units | cross-check vs sales comps and replacement cost |
| Debt service coverage (DSCR) | NOI ÷ ADS | lender min 1.20–1.25 (multifamily 1.20, commercial 1.25, office 1.30+); < 1.10 = NO-GO on Conservative |
| Debt yield | NOI ÷ loan amount | lender floor 8–10%; sanity check independent of rate |
| Loan-to-value (LTV) | loan ÷ price (or appraised value) | banks 65–75%; SBA 504 up to 90% owner-occupied; DSCR lenders 65–75% |
| Cash-on-cash (CoC) | CFBT ÷ total equity in (incl. closing, reserves, TI/LC, acq fee) | hurdle: ≥ 8% Conservative for GO; 6–8% CONDITIONAL |
| Break-even occupancy | (OpEx + reserves + ADS) ÷ GPI | > 85% is thin; > 90% is fragile |
| Equity multiple | (Σ CFBT + net sale proceeds) ÷ total equity | ≥ 1.75x over 5 yrs targeted |
| IRR (levered) | rate that zeros equity out vs CFBT + sale | ≥ 15% targeted, projected, not guaranteed |
| Negative leverage | cap rate < loan constant | flag in red; only acceptable with a verified value-add path |
| Loan constant | ADS ÷ loan amount | for comparison to cap rate |
| Exit value | NOI Year N+1 ÷ exit cap | exit cap = entry cap + 50 bps unless verified otherwise (never lower than entry) |

## Financing conventions (defaults the script uses unless the run verifies something else)
| Structure | LTV | Rate (verify per run) | Amort | Term | Notes |
|---|---|---|---|---|---|
| Bank / credit union commercial | 70–75% | prime-based or 5-yr Treasury + 2.25–3.00% | 25 yr (20 yr office) | 5/7/10 yr balloon | recourse, DSCR ≥ 1.25 |
| Agency multifamily (Fannie/Freddie small balance, 5+ units) | 75–80% | 10-yr Treasury + spread | 30 yr | 5/7/10 yr | non-recourse, ≥ 90% occupancy 90 days, DSCR 1.25 |
| DSCR / non-QM (1–4 and some 5–8 unit) | 65–75% | higher than bank | 30 yr | 30 yr | property-only qualification |
| SBA 504 (owner-occupied ≥ 51%) | 90% (50% bank + 40% CDC) | bank rate + debenture ~ Treasury + ~1.5% | 25 yr | 25 yr | ~10% equity; 504 for real estate, 7a if working capital too |
| Seller finance (first position) | negotiated, model 70–90% | 5–7% IO | interest-only | 3–7 yr balloon | P.A.T.H. default: interest-only, first position first |
| Seller carry second | 10–20% behind a bank first | 6–8% IO | IO | matches first | bank must permit; lender counts it in combined DSCR |
| Private money | 60–70% | 9–12% + points | IO | 12–36 mo | bridge to stabilization then refi |
| All cash | 0% | — | — | — | unlevered yield = cap rate |

Model **Option A (Equity JV partner)** and **Option B (Private money lender)** for the capital
stack section per the P.A.T.H. standard, then a Recommended Path.

## Sensitivity (always in the report)
- Grid 1: **NOI × exit cap** → value and equity multiple.
- Grid 2: **interest rate × vacancy** → DSCR (the lender's stress test; show where DSCR crosses 1.25 and 1.10).
- Grid 3: **purchase price** at −10%, −5%, ask, +5% → CoC and DSCR (tells Phil where the offer needs to land).

## Words for the report
Returns are "projected", "targeted", "potential", and "not guaranteed". Never "will return",
"guaranteed", "safe". The report is for discussion purposes only — not legal, tax, or financial advice.
