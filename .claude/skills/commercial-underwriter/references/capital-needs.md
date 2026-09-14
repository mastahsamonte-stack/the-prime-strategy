# Capital Needs — "How Much Will I Need?"

The most common question Phil asks. The answer is a **sources & uses** table that reconciles to the
dollar, with the acquisition fee inside it. Think of it as the packing list for the trip: the
purchase price is the plane ticket, but you still need the hotel, the meals, and the emergency cash.

## Uses (what the money is spent on)
| Line | Default | Notes |
|---|---|---|
| Purchase price | ask, or the price the offer lands at | run the −10% / −5% grid |
| Closing costs | **2.5–4.0% of price** commercial (title, transfer tax, lender fees, appraisal $3–8K, environmental Phase I $2–4K, survey, legal $5–15K) | multifamily 5+ ~2.5%; SBA adds ~2.5–3.0% in fees, often financed |
| Loan points / origination | 0.5–1.0% bank; 1–3% private money | included in closing if the lender quote bundles it |
| TI / leasing commissions (TI/LC) | vacant SF × TI $/SF + first-year rent × 4–6% (LC) | TI by class: retail $10–25, office $15–40 (2nd gen), MOB $40–100, industrial $2–8; verify local |
| Immediate capex | inspection-driven: roof, HVAC, parking lot, ADA, code | PCA (property condition assessment) $2–5K itself; never zero on a building > 20 yrs old without a PCA |
| Lease-up carry | months of (OpEx + ADS) uncovered by in-place income while filling vacancy | Conservative: 6–12 months of the shortfall |
| Working-capital / operating reserve | **3–6 months of OpEx + ADS** | lenders often require 6 months; interest reserve if IO bridge |
| Lender-required reserves | replacement reserve escrow, tax & insurance escrow at closing (2–6 months) | ask the lender; default 3 months T&I |
| **Acquisition fee** | **~7.47% of total capital raised** | P.A.T.H. standard; always a line; paid at closing to P.A.T.H. Operation |
| **Total uses** | Σ | |

## Sources (where the money comes from)
| Line | |
|---|---|
| First-position debt | LTV × price (or LTC × total cost, whichever the lender uses; bank usually the lesser of LTV and DSCR-constrained loan) |
| Second-position debt (seller carry / private) | if any |
| SBA CDC debenture | 40% of eligible project cost, 504 only |
| **Equity raise** | plug: total uses − all debt. This is "how much P.A.T.H. Operation needs" |
| **Total sources** | must equal total uses |

**Acquisition fee circularity:** the fee is a % of the raise and is itself a use, so
`raise = (uses_before_fee − debt) ÷ (1 − fee%)`. The script handles this; do not hand-compute.

**DSCR-constrained loan:** the lender sizes the loan as the lesser of LTV × value and the loan whose
ADS gives DSCR = 1.25 on THEIR NOI. If the DSCR-sized loan is smaller than LTV × price, the equity
need rises by the difference. Always show both and use the smaller.

## The three numbers Phil wants in chat
1. **Cash to close** = equity raise (includes closing, TI/LC, capex, reserves, fee).
2. **Of which, down payment** = price − debt.
3. **Of which, everything else** = closing + TI/LC + capex + reserves + fee.

Show the equity need under the Conservative case, then under Option A (equity JV) and Option B
(private money) so the cap table and the lender ask are both visible.

## MARKET mode sizing
For each of the three representative sizes in `asset-classes.md`, compute price (NOI ÷ market
cap), then run the same uses/sources with default closing %, benchmark TI/LC for benchmark vacancy,
a capex allowance of $5/SF (multifamily $3,000/unit) as a placeholder labeled `[ASSUMPTION]`, 6
months reserve, and the acquisition fee. The output is a table: size → price → NOI → loan → equity
needed → DSCR → CoC. This is the "what would I need for a strip center in this town" answer.

## Diligence items that change capital needs (put in the checklist)
Phase I environmental (Phase II if flagged), PCA, roof and HVAC age, ADA survey, zoning letter,
certificate of occupancy for each use, estoppels from tenants > 10% GPR, SNDA from lender, title
with easements and ROFRs, survey, tax reassessment estimate from the assessor, insurance quote (flood
zone, wind, age of building), utility bills 12 months, service contracts, litigation search on tenants
and seller, personal property list.
