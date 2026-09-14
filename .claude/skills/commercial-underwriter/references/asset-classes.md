# Asset Classes — What Changes When the Class Changes

Read this first in Step 1. It tells you which facts matter, how rent is quoted, what the lease
usually pushes onto the tenant, and the sanity bands for expenses, vacancy, and cap rates.

**⚠ BENCHMARKS ARE PRIORS, NOT DATA.** Every band below is for spotting a suspicious OM number.
No band enters the model until it has walked the accuracy-guardrails ladder for THIS submarket.
A figure outside its band → mandatory deep-dive before use.

## How commercial rent is quoted (get this right or the whole model is off)
| Quote style | Meaning | Convert to annual rent |
|---|---|---|
| `$18/SF/yr NNN` | Tenant pays base rent PLUS its share of taxes, insurance, CAM | SF × 18 (recoveries modeled separately) |
| `$18/SF/yr gross` or `full-service` | Landlord pays operating expenses out of the rent | SF × 18 (no recoveries; expenses fully on landlord) |
| `$18/SF/yr modified gross (MG)` | Landlord pays some (often taxes/insurance), tenant pays some (often utilities/janitorial) | SF × 18; model only the recoveries the lease names |
| `$1.50/SF/mo` (common in CA, AZ, NV, WA) | Monthly rate | SF × 1.50 × 12 |
| `$1,450/mo` per unit (multifamily) | Per-door monthly | units × rent × 12 |
| Industrial `$0.85/SF/mo NNN` | Monthly, usually NNN | SF × 0.85 × 12 |

Rentable SF (RSF) vs usable SF (USF): office rent is on RSF, which includes a load factor of
10–20% for common areas. If the OM quotes USF, ask which. Multi-tenant buildings: sum tenant RSF,
compare to gross building area (GBA); a gap > 15% is a question for the broker.

## Class table
| Class | Rent basis | Typical lease | Expense ratio (of EGI) | Vacancy band | Cap band (2025-26, secondary/tertiary markets) | Lead facts | Class-specific killers |
|---|---|---|---|---|---|---|---|
| **Multifamily 5+ units** | $/unit/mo by bedroom | 12-mo gross; tenant pays electric, often gas | 35–50% (older, landlord-paid heat = high end) | 4–8% + 1–2% credit loss | 5.5–7.5% | unit mix, in-place vs market rent by unit, utility split, rent control, deferred capex (roof, boilers, windows) | rent control / just-cause laws, lead paint, undersized tax escrow after reassessment |
| **Retail strip / neighborhood center** | $/SF/yr NNN | 3–10 yr NNN with 2–3% bumps or CPI | 10–25% landlord non-recoverable; total OpEx 25–35% before recoveries | 7–12% | 6.5–8.5% | anchor + co-tenancy clauses, traffic count, parking ratio (4–5/1,000 SF), % of rent from top 3 tenants, exclusive-use clauses | anchor vacancy triggers co-tenancy rent cuts, restaurant grease/venting capex, single-tenant > 40% of GPR |
| **Single-tenant NNN (QSR, dollar store, pharmacy, auto)** | $/SF/yr absolute NNN | 10–20 yr, corporate or franchisee guarantee | 0–5% (absolute NNN) to 10% (NN, roof/structure on landlord) | 0% until expiry, then binary | 5.0–7.0% credit tenants; 7.0–9.0% franchisee / short term | guarantor credit, remaining term, options, rent bumps, dark-store risk, re-tenanting cost | < 5 yrs remaining with no options, franchisee guarantor with 1–2 stores, single-purpose building (bank vault, drive-thru only) |
| **Office (suburban B/C)** | $/SF/yr full-service or MG | 3–7 yr, TI $10–$40/SF new, $5–$15 renewal | 40–55% full-service (landlord pays everything) | 12–20% (2025-26 office vacancy is elevated; verify locally) | 8.0–11.0% | RSF/USF, parking, HVAC age, elevator, ADA, % medical or government tenants, WALT | rollover > 30% inside loan term, obsolete floor plates, HVAC end-of-life, sublease competition |
| **Medical office (MOB)** | $/SF/yr NNN or MG | 5–10 yr, heavy TI ($40–$100/SF buildout) | 30–45% | 6–10% | 6.5–8.0% | hospital affiliation, specialty (imaging, dental, dialysis = sticky), buildout ownership, ADA | tenant leaves and buildout is single-use, hospital system consolidation |
| **Industrial / warehouse / flex** | $/SF/yr NNN (or $/SF/mo) | 3–10 yr NNN, bumps 3% | 5–15% (NNN) ; 20–30% flex MG | 3–7% (verify; some markets softened 2024-26) | 6.0–8.0% | clear height (≥ 24' modern, < 16' obsolete), dock-high vs grade doors, truck court, power (3-phase amps), sprinklers, office % | low clear height, no truck turning radius, environmental (prior auto/chemical use), zoning non-conforming |
| **Mixed-use (retail down, residential up)** | retail $/SF/yr; residential $/unit/mo | blended | 35–45% blended | blended by component | 6.5–8.0% | separate the two rent rolls, separate utility metering, ground-floor tenant type, residential entry separate from retail | commercial vacancy dragging a residential-driven price, unpermitted units |
| **Self-storage** | $/SF/mo by unit size, occupancy-managed | month-to-month | 30–40% | 8–15% physical, economic vacancy higher (discounts) | 6.0–7.5% | unit mix, climate-controlled %, street rate vs in-place, rate-management history, competition within 3 miles | new supply within 3 miles, in-place rates far above street |
| **Small bay / contractor flex** | $/SF/yr NNN or MG | 1–3 yr, small tenants | 20–30% | 8–12% | 7.0–9.0% | roll-up doors, unit sizes 1,000–3,000 SF, tenant count | many tiny tenants = management burden, code issues with residential use inside units |

Hospitality, senior housing, and licensed care are NOT this skill: route hotels to a hospitality
underwriter (none installed yet — say so), ALF/IDD/SIL/RTC to their own skills, and MHP/RV to
mhp-rv-underwriter.

## Representative sizes for MARKET mode
When Phil gives a city and class with no property, size three buildings so the "how much do I
need" answer is concrete:
| Class | Small | Medium | Large |
|---|---|---|---|
| Multifamily | 6 units | 12 units | 24 units |
| Retail strip | 6,000 SF | 12,000 SF | 25,000 SF |
| Single-tenant NNN | 2,500 SF | 5,000 SF | 10,000 SF |
| Office B/C | 8,000 SF | 20,000 SF | 40,000 SF |
| Industrial / flex | 10,000 SF | 25,000 SF | 60,000 SF |
| Mixed-use | 2 retail + 4 res | 3 retail + 8 res | 4 retail + 16 res |
| Self-storage | 20,000 NRSF | 45,000 NRSF | 80,000 NRSF |

Price each size at verified market rent × size, less benchmark vacancy and expenses, capitalized
at the verified market cap rate, then cross-check against price/SF of recent sales. Both methods
must land within 15% or the report flags the gap.

## Owner-occupant flag (SBA 504 / 7a)
If a P.A.T.H. operating use (or a known tenant Phil controls) could occupy ≥ 51% of the building,
flag SBA 504 in the financing section: ~10% down, 50% bank first, 40% CDC debenture, 25-year
fixed on the debenture. This changes "how much do I need" dramatically and belongs in the
Recommended Path discussion. Investment (non-occupied) property does not qualify.
