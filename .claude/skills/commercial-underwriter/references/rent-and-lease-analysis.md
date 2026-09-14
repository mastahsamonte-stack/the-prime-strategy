# Rent Roll and Lease Analysis — Reading the Revenue Ledger

The rent roll is the business's customer list. Every line is a contract with a start, an end,
a price, and terms about who pays the building's bills. This file tells you how to abstract it,
mark it to market, and turn it into the income inputs the script needs.

## 1. Lease abstract table (one row per space, vacant spaces included)
| Tenant | Suite | RSF (or unit type) | In-place rent | Basis | Market rent | Lease type | Start | Expiry | Options | Bumps | Recoveries | Guarantor | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Rules:
- Convert every rent to **annual $ and $/SF/yr** (or $/unit/mo for residential). Show both.
- `Basis` = NNN / NN / MG / full-service / gross. If the OM says "NNN" but the expense statement shows
  landlord paying taxes, the OM is wrong; model what the money actually does.
- **Vacant** spaces go in the table at $0 in-place and market rent in the market column. They are
  the value-add.
- **Month-to-month** = treat as expiring in 30 days for rollover purposes.
- Percentage rent, CPI bumps, free-rent burn-off, and TI amortized into rent are noted separately;
  do not blend them into base rent.

## 2. Metrics to compute from the abstract
- **Occupancy (physical)** = occupied SF ÷ total RSF. **Economic occupancy** = collected rent ÷ GPR.
- **WALT** (weighted average lease term, years) = Σ(remaining term × annual rent) ÷ Σ annual rent.
  WALT shorter than the loan term is a lender question; WALT < 2 years on a single-tenant deal is a killer.
- **Rollover schedule**: % of GPR expiring in each of the next 5 years. Anything > 30% in one year
  inside the loan term requires a lease-up reserve in capital needs.
- **Mark-to-market gap** = Σ(market rent − in-place rent) for occupied space. Positive gap = upside
  (Base/Upside cases only, realized on expiry, not day one). Negative gap = rent roll is above market,
  meaning the "upside" is a downside at rollover. Flag prominently.
- **Tenant concentration** = top tenant % of GPR and top 3 % of GPR. > 40% single tenant is
  effectively a single-tenant deal; underwrite the guarantor.
- **Recovery income** (NNN/MG) = Σ tenant pro-rata share × recoverable expenses × occupancy.
  Never assume 100% recovery: vacant space's share is the landlord's, and caps/exclusions in the
  lease reduce it. Conservative default = recoverable expenses × physical occupancy × 0.9.

## 3. Finding market rent for a location (order of preference)
1. **Verified-claims memory and the commercial cache** (`research-playbook.md`) — reuse if < 6 months.
2. **Individual comparable listings** — LoopNet, Crexi, brokers' sites, Craigslist commercial,
   Zillow/Apartments.com for multifamily. Pull 3–6 comps within the submarket, same class, similar
   size and age. Record each: address, SF, asking rent, basis, date. Asking rent is a ceiling; take
   5–10% off for effective rent unless the market is tight (verify).
3. **Recent executed leases** — broker market reports (CBRE, Colliers, Cushman, JLL, Marcus &
   Millichap, local brokerages), county deed records for lease memoranda, and a broker call.
4. **Public data** — HUD Fair Market Rents and census ACS median rent for multifamily floor checks;
   city economic-development pages for retail/industrial absorption.
5. **Ladder rung 4** — deep-dive subagent (call two brokers, pull three more comps) before any figure
   is 🔴.

Write the comp table into the report and into memory. Every comp gets a source and a date.

## 4. Underwriting rent (what actually enters the model)
| Case | Occupied space | Vacant space | Vacancy factor |
|---|---|---|---|
| **Conservative** | in-place rent, no bumps beyond signed | stays vacant OR leases at 90% of market after a 6–12 month carry, with TI/LC funded in capital needs | verified submarket vacancy, min 5% (min 7% office/retail) |
| **Base** | in-place, marked to market on expiry only | leases at market after carry | benchmark for class |
| **Upside** | mark-to-market on expiry, bumps applied | leased at market within 6 months | benchmark minus 2 pts |

The verdict is judged on **Conservative**. Base and Upside are shown so Phil sees what he is buying
versus what he is being sold.

## 5. Lease red flags to read for
- Co-tenancy clauses (retail): rent drops if the anchor leaves.
- Early termination rights, kick-outs, or ROFR/ROFO on the building.
- Exclusive-use clauses that block re-tenanting a vacant bay.
- Landlord obligations hiding in "NNN": roof, structure, parking lot, HVAC replacement.
- Free rent or TI not yet burned off (the seller is showing gross rent).
- Below-market long-term leases to a related party of the seller.
- Estoppels: require them from every tenant > 10% of GPR before closing (diligence checklist).
