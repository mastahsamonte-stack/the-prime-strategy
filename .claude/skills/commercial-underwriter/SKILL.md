---
name: commercial-underwriter
description: Underwrites a commercial income property (office, retail, industrial/flex, 5+ unit multifamily, mixed-use, self-storage, medical office, single-tenant NNN) from an address, city, listing, OM, or rent roll. Researches market rents per SF and per unit, vacancy, cap rates, expense benchmarks, taxes and lease comps for that location; models GPR, EGI, OpEx, NOI, debt service, DSCR, debt yield, cap rate, cash-on-cash, 5-year proforma, IRR and equity multiple; and sizes the capital needed (down payment, closing costs, TI/LC, capex, reserves, acquisition fee) as a full sources and uses. Delivers a GO / CONDITIONAL / NO-GO HTML report. Triggers on "commercial-underwriter", "underwrite this commercial property", "what are commercial rents in [city]", "how much do I need for this building", "does this strip center pencil", "run the numbers on this office / retail / warehouse", or any commercial address, OM, or LoopNet/Crexi link paired with an underwriting, rent, or capital question.
version: 1.0.0
author: P.A.T.H. Operating Co.
---

# Commercial Underwriter

**Version 1.0 | September 14, 2026** — first release. Built with phil-skill (DBS) and modeled on
mhp-rv-underwriter so the discipline is identical across asset classes: verify the numbers, model
the upside conservatively, size the capital stack with the acquisition fee, stress the debt, give a
clear verdict.

## What this skill does

Phil hands it a **location** (address, city, or submarket), an **asset class** (or lets the skill
detect one from a listing/OM), and optionally a **rent roll, OM, or T-12**. It answers three
questions with numbers a lender or JV partner can check:

1. **What are the rents?** Market rent for that location and class, per SF per year (commercial)
   or per unit per month (multifamily), plus vacancy, lease type, and expense benchmarks.
2. **What is it worth and does it pencil?** GPR → EGI → NOI → debt service → DSCR, debt yield,
   cap rate, cash-on-cash, 5-year proforma, IRR, equity multiple, break-even occupancy.
3. **How much will P.A.T.H. Operation need?** Down payment, closing costs, TI/LC, capex, reserves,
   and the ~7.47% acquisition fee, reconciled as sources = uses.

Analogy for Phil: a commercial building is a **small business that sells space**. The leases are its
customer contracts, the rent roll is its revenue ledger, the operating statement is its P&L, and NOI
is its profit before the mortgage. Underwriting is auditing that business before buying it.

**Worth it because:** a commercial deal takes 3–5 hours of manual research and modeling per run and
Artemis surfaces commercial leads weekly; this brings it to ~20 minutes with the verification baked in.

**Modes** (detect from the intake, state the mode in the report header):
- **DEAL mode** — a specific property with a price (address + listing/OM/rent roll). Full 16-section report.
- **MARKET mode** — a location + asset class with no specific property ("what would I need for a
  small strip center in Lowell?"). Produces a Market Underwriting Sheet: rents, expenses, cap rate,
  what a typical building of 3 sizes costs, and the equity needed at each size. Same verification rules.

---

## Standing Rules (from CLAUDE.md — these win on conflict)
- **HTML default output** — self-contained single-file `.html`, inline CSS. Exceptions: spreadsheets
  where formulas are the point, source images, raw `.csv`/`.json` data files. When in doubt, generate
  an HTML wrapper alongside.
- **File versioning** — `Commercial_Underwriting_<Street-or-City>_v1.0_<YYYY-MM-DD>.html`; updates
  increment version + date and save as a NEW file (never overwrite); version stamp banner inside every
  report; Reason-for-Update block on every v1.1+.
- **Save to `~/Cowork/` root** — overrides any other default path. Always tell Phil the full path plus
  the headline number and the GO / CONDITIONAL / NO-GO verdict in chat.
- **P.A.T.H. Operation naming** — the acting party in all report content is "P.A.T.H. Operation",
  never "Phil". Chat still addresses Phil.
- **Acronym Index** — one consolidated index at the very END of every report, alphabetical, every
  acronym used anywhere in the report. Read `memory/acronyms-by-domain.md` for consistent definitions.
- **NO AUTO-EMAIL** — never create Gmail drafts or send email as a delivery step.
- **Investor-safe language** — "targeted", "projected", "potential", "not guaranteed". Never
  guaranteed-return language.
- **Acquisition fee ~7.47% of total capital raised** — always a line in sources & uses; reconcile the stack.
- **Fact-check subagent (Aletheia) runs before assembly** — HARD GATE.

*If CLAUDE.md and this file ever conflict, CLAUDE.md wins.*

---

## Workflow

### Step 0 — Accuracy ladder, memory-first, Council gate (before any web search)
1. Read `~/Cowork/skills-overrides/accuracy-guardrails.md`. Every material figure in this run
   (market rent, vacancy, cap rate, expense line, tax bill, TI/LC cost, loan terms) walks the ladder
   in order: **verified-claims memory → primary-source web research → second brain
   (`olympus-vault/` + `VADER/`) → deep-dive subagent → 🔴 NEEDS MORE DATA** (conservative
   placeholder labeled `[ASSUMPTION — pending verification]`, verdict capped at CONDITIONAL).
2. Memory first: check `projects/program-memory/verified-claims.md` and the commercial cache
   described in `references/research-playbook.md` (section "Memory schema"). Entries under 6 months
   old render ✓ and skip re-research. Stale entries are reused but marked ⚠ STALE and refreshed if quick.
3. **Council gate (Stage 2.5):** in DEAL mode, look for `Council_Ruling_*` for this deal in
   `~/Cowork/`. If found, model its 🔒 LOCKED ASSUMPTIONS and note deviations. If none: tell Phil
   the Council has not ruled and pause; proceed only on Phil's explicit "skip the council".
   MARKET mode has no Council gate (nothing to commit to yet).
4. **Ground-truth rule:** anything Phil provided (price, rent roll, seller terms, condition, his own
   statements) is never challenged and gets ✓. Seller/broker OM numbers are inputs to verify, not facts.

### Step 1 — Parse the intake and classify
Load `references/asset-classes.md`. Detect the asset class and the intake type:

| Intake | Handling |
|---|---|
| Address only | Research the parcel: use, building SF, lot, year built, assessed value, taxes, owner, last sale, zoning (county assessor + GIS first). Listing sites are client-rendered — use Chrome MCP `navigate` + `get_page_text`, never raw fetch. |
| Listing link (LoopNet / Crexi / broker site) | Open via Chrome MCP, extract price, SF, units, NOI claimed, cap claimed, lease summary, then enrich with the address research above. |
| OM / rent roll / T-12 (PDF or pasted) | Parse every tenant, SF, rent, lease type, start/expiry, options, recoveries; every expense line. Treat as **claims to verify** unless Phil says they are his own numbers. |
| City / submarket + class only | MARKET mode. Skip parcel research; go straight to Step 2 with three representative sizes from `references/asset-classes.md`. |

Extract (DEAL mode): name, address, class, building SF / units, lot, year built, occupancy, asking
price, price/SF or price/unit, claimed NOI and cap, lease types, WALT, rollover in the next 36 months,
owner-occupancy potential (SBA 504 flag), condition flags, and any seller-financing signal.
Missing fact → "unknown — verify", never a guess.

### Step 2 — Market research (only what memory did not have)
Follow `references/research-playbook.md` step by step. For the location and class, pull:
- **Market rent** (per SF/yr NNN or gross for commercial; per unit/mo by bedroom for multifamily)
  from at least 3 comparable active listings or recent leases within the submarket, cited individually.
- **Vacancy / absorption** for the submarket and class.
- **Cap rate** band for the class in this submarket (recent sales comps, broker reports).
- **Expense benchmarks** for the class, plus the actual tax bill (assessor), insurance quote range,
  utility structure, and the likely reassessment on sale.
- **Lease comps:** who pays what (NNN / modified gross / full-service), typical TI and free rent,
  lease term, escalations, and CAM recovery norms.
- **Demand drivers and risks:** employers, traffic counts (retail), truck access and clear height
  (industrial), population and income (multifamily), rent control or commercial-tenant laws.
- **Replacement cost** sanity check (price/SF vs cost to build).

Verification standard: PRIMARY source (assessor, GIS, official rate data, individual listings as raw
comps) or TWO independent sources agreeing. One blog or aggregator is never enough. Every material
figure carries source name + date into the report. Write every newly verified figure back to
`projects/program-memory/verified-claims.md` and the commercial cache BEFORE Step 5.

### Step 3 — Analyze the rent roll and mark to market
Load `references/rent-and-lease-analysis.md`. Build the lease abstract table (tenant, SF, current
rent, market rent, lease type, expiry, options, recoveries), compute WALT, the rollover schedule, the
mark-to-market gap, and the recovery income. In MARKET mode, build a representative rent roll for each
of the three sizes at market rent with benchmark vacancy.

### Step 4 — Run the model (Solutions script — do not hand-compute)
Load `references/underwriting-model.md` for definitions and the lender conventions, then:
1. Write the deal to JSON in the schema printed by `python3 scripts/underwrite.py example <class>`.
2. Run `python3 scripts/underwrite.py model deal.json --out model.json --tables tables.html`.
3. Run the **Conservative** case first (in-place rents, verified vacancy, verified expenses, current
   taxes reassessed at purchase price). Then **Base** (mark-to-market on rollover only, benchmark
   vacancy) and **Upside** (lease-up / value-add plan). The verdict is judged on Conservative.
4. Capital needs come from `references/capital-needs.md` and are inputs to the same script run
   (closing %, TI/LC, capex, reserve months, acquisition fee %). Sources must equal uses.
5. MARKET mode: run `python3 scripts/underwrite.py size sizing.json --tables tables.html` for the
   three representative sizes.

Financing structures the script supports: bank/credit-union commercial, DSCR, seller finance
(interest-only first position), SBA 504 (owner-occupied ≥51%), all cash, plus an optional second
position (seller carry, private money). Model Option A (Equity JV partner) and Option B (private
money lender) per the P.A.T.H. standard.

### Step 5 — Fact-check HARD GATE (report assembly may not begin until it returns)
Spawn the Aletheia fact-check subagent (Agent tool) on the research + model draft. It re-walks every
material figure up the ladder: market rents, vacancy, cap rate, tax reassessment, expense lines, TI/LC,
loan terms, demand claims. Phil-provided items get ✓ automatically. Render: ✓ verified, ⚠ conflicting
(downstream math uses the more conservative value, "pending ruling" via gospel-review), 🔴 needs more
data (conservative `[ASSUMPTION]`, "who to call" line, verdict capped at CONDITIONAL). Anything
unverifiable must go through a deep-dive subagent (ladder rung 4) before it may be called 🔴.
Only bypass: Phil says "skip fact-check" or "quick and dirty" for this run.

### Step 6 — Assemble the report
Follow `references/report-structure.md` exactly (16 sections, PATH color palette, verdict band,
version stamp, Cash-Flow Optimization section, Fact-Check Summary, Acronym Index, footer). Embed the
tables from `tables.html`; write the narrative around them. Save to `~/Cowork/` root with the
versioned filename. In chat, give Phil: address or market, class, size, price (or typical price at
three sizes), Conservative NOI and cap, DSCR, cash-on-cash, total capital needed including the
acquisition fee, and the verdict.

---

## Verdict rules (Conservative case governs)
- **GO** — DSCR ≥ 1.25 on Conservative, debt yield ≥ 8%, cash-on-cash ≥ the P.A.T.H. hurdle in
  `references/underwriting-model.md`, no 🔴 on a verdict-driving figure, no unresolved rollover > 30%
  of GPR inside the loan term without a lease-up reserve.
- **CONDITIONAL** — pencils only with a named condition (price cut, seller carry, lease-up reserve,
  tax abatement, verified rent above in-place), or any verdict-driving figure is 🔴 / ⚠.
- **NO-GO** — DSCR < 1.10 on Conservative, negative leverage with negative cash flow and no
  credible value-add, or a structural killer (environmental, zoning, single tenant with < 2 years
  and no replacement demand). The script prints its math-only read as `verdict(script)`; Claude
  applies the 🔴 cap and the structural killers on top of it.

## Self-check before delivering (all must PASS)
1. **Gates ran** — accuracy ladder read; memory-first done; Council gate checked (DEAL mode);
   fact-check returned before assembly; benchmarks used only as sanity bands.
2. **Sections complete** — all 16 sections + Cash-Flow Optimization + Acronym Index, in order.
3. **Sources cited** — every material figure carries ✓/⚠/🔴 + source; Fact-Check Summary shows counts.
4. **Math reconciles** — script output used, sources = uses including the acquisition fee, DSCR never
   rounded up, verdict judged on Conservative, tax reassessment applied.
5. **Standing rules met** — HTML, versioned filename + stamp, P.A.T.H. Operation, `~/Cowork/` root,
   investor-safe language, no email.
Any FAIL → fix before presenting.
