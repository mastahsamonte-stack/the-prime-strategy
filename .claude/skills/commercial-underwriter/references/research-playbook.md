# Research Playbook — What to Pull for a Location, in What Order, From Where

Run this in Step 2. The order matters: memory first, primary sources second, aggregators last.

## 0. Memory schema (read before any search; write after verification)
Cache path: `projects/program-memory/commercial-cache/` (fall back to
`~/Cowork/projects/Commercial Underwriter/_cache/` if the program-memory path is not writable;
say which one in the report so the next run looks in the same place).

```
commercial-cache/
├── INDEX.md                             one line per cached submarket+class
├── <ST>-<city-or-submarket>-<class>.md  e.g. MA-lowell-retail.md, AZ-phoenix-west-industrial.md
└── <ST>-<county>-taxes.md               assessment ratio, mill rate, reassessment-on-sale rule
```

Per-file front matter: `market`, `class`, `state`, `county`, `verified_date`, `source_runs`. Body
holds: market rent (with 3–6 comps, each with address, SF, rent, basis, date, source), vacancy,
cap rate band with 2–3 sales comps, expense benchmarks used, TI/LC norms, lender terms quoted,
demand notes, risks, and a "who to call" list. Freshness window: **6 months** for rents/cap rates,
**12 months** for tax rules and zoning. Stale → reuse, mark ⚠ STALE, refresh the headline figures.

Also write every verified figure to `projects/program-memory/verified-claims.md` in the standard
format (figure, value, source, date, run) so Aletheia and other skills can reuse it.

## 1. The parcel (DEAL mode only) — primary sources
| Need | Where | Notes |
|---|---|---|
| Owner, assessed value, tax bill, last sale | county assessor / treasurer site | MA: town assessor + MassGIS; AZ: county assessor; TX: CAD; CA: county assessor + Prop 13 |
| Building SF, year built, lot, use code | assessor property card | the OM's SF often differs; report both |
| Zoning + permitted uses + parking ratio | city/county GIS + zoning ordinance | screenshot the zoning map layer; note overlay districts |
| Flood zone | FEMA flood map service center | insurance driver |
| Environmental | state environmental agency site lookup (MA: MassDEP; CA: GeoTracker; EPA Envirofacts) | prior gas station / dry cleaner / auto = Phase II risk |
| Permits and violations | city building department portal | open permits, unpermitted work |
| Traffic count (retail) | state DOT traffic count map | AADT on the frontage road |
| Demographics | Census ACS 5-yr (population, median HH income, renters %) for the tract and 1/3/5-mile rings | multifamily and retail demand |

## 2. Market rent and vacancy (all modes)
1. Memory / cache.
2. **Comps** — LoopNet, Crexi, Apartments.com/Zillow (multifamily), local broker sites, Craigslist
   commercial. Use Chrome MCP `navigate` + `get_page_text` (client-rendered). Record 3–6 comps per
   class in the submarket. Same-class, similar-size, within 3 miles (urban) or 10 miles (suburban/rural).
3. **Broker market reports** — search `"<metro>" "<class>" market report Q<n> 2026` for CBRE, Colliers,
   Cushman & Wakefield, JLL, Marcus & Millichap, NAI, Kidder Mathews, Lee & Associates, and local
   firms. Pull asking rent, vacancy, absorption, under-construction SF.
4. **Public floors** — HUD FMR and ACS median rent (multifamily); city EDC pages.
5. Two sources must agree within 10% or the figure is ⚠ and the conservative one is used.

## 3. Cap rates and values
- Sales comps: LoopNet/Crexi "sold" filters, county deed records with price, broker "recent
  transactions" pages, CoStar via a broker call if available.
- Broker cap-rate surveys (CBRE Cap Rate Survey, Marcus & Millichap class reports) as the band.
- Replacement cost: RSMeans-style $/SF for the class (verify), plus land value from assessor.
- Price/SF or price/unit vs the last 3 sales in the submarket.

## 4. Expenses
- Taxes: assessor bill + county assessment ratio + mill/levy rate → reassessed estimate at price.
- Insurance: two quotes or the state's commercial property rate benchmark; flood/wind/age loadings.
- Utilities: 12 months of bills if the OM has them; otherwise class benchmark and metering structure.
- Management: local PM company fee quotes (2 calls or published rates).
- Everything else: class benchmark bands from `asset-classes.md`, sanity-checked against the OM.
  OM expenses more than 20% below benchmark are ⚠ and the benchmark is used.

## 5. Lease comps and TI/LC
Broker reports and 2 broker calls: typical term, escalations, free rent, TI allowance, LC %.
Record for the class and submarket in the cache.

## 6. Debt terms
Two lender data points per run: a local bank or credit union rate sheet / call, and an agency or
DSCR quote if multifamily. SBA 504 debenture rate from the CDC site if owner-occupant applies.
Record rate, LTV, amort, term, recourse, DSCR floor, reserves required.

## 7. Demand and risk layer
Employers and announcements (city EDC, local business journal), new supply under construction,
rent control / commercial-tenant protection laws (verify by state and city), crime map, transit.

## 8. Who to call (put in the report)
Assessor, planning/zoning desk, building department, two commercial brokers active in the class,
one lender, one insurance agent, one PM company. Phone numbers from official pages.

## Verification standard
Primary source or two independent sources agreeing. Every figure: source name + date. A number
with no source is ⚠. Ladder rung 4 (deep-dive subagent) runs before any figure is called 🔴.
Ground truth from Phil is never challenged.
