# The Prime Strategy — Curated Agent Roster

A hand-picked subset of [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) (MIT, 296 agents) trimmed to the 71 that support Phil's operating system: creative-finance real estate acquisition, licensed residential care (SIL, ALF, IDD, sober living, coliving), lead hunting and CRM nurture, grant funding, content distribution, and the Claude Code skill stack that runs it all.

Files in `.claude/agents/` are verbatim copies from upstream (snapshot 2026-09-05) so they can be refreshed by re-copying. Original license: `LICENSE-agency-agents`.

## How this fits the existing system

The skills you already run (deal-analyzer, aged-out-sil, alf-senior, artemis, apollo, council, aletheia, and so on) are **playbooks**: step-by-step procedures with your rates, your vault, your voice. These agents are **personas**: who Claude should be while executing a step. A playbook says "underwrite this SIL house". A persona says "think like a controller while you build the expense tab". Use them inside skills, not instead of them.

## Use

Inside this repo, every agent in `.claude/agents/` is available automatically as a project subagent. To make them available everywhere:

```bash
./scripts/install.sh                 # all 71 into ~/.claude/agents
./scripts/install.sh finance sales   # one or more divisions only
```

Then in any session: `Use the Loan Officer Assistant agent to pre-qualify this borrower.`

Context note: every installed agent adds a line to the subagent list Claude reads each turn. Install globally only the divisions you use daily and leave the rest project-scoped here.

## The picks

### Engineering (5 of 59)
| Agent | Why it helps | Pairs with |
|---|---|---|
| Prompt Engineer | Tightens skill prompts and trigger phrases before they ship | skill-creator, dbs-framework, phil-skill |
| Multi-Agent Systems Architect | Designs handoffs, trust boundaries, and failure recovery for council, devils-advocate, and aletheia pipelines | council, devils-advocate, zeus |
| Email Intelligence Engineer | Turns forwarded deal emails and broker threads into structured fields | deal-analyzer, buy-this, email-triage |
| Data Visualization Engineer | Honest charts for the HTML investor reports | every feasibility and underwriting skill |
| Rapid Prototyper | Landing pages, lead-magnet pages, quick dashboards | landing-page, lead-magnet-builder, web-artifacts-builder |

### Specialized (5 of 58)
| Agent | Why it helps | Pairs with |
|---|---|---|
| Chief of Staff | Filters noise, routes work, enforces the operating cadence | morning, eos-strety, zeus |
| Loan Officer Assistant | Borrower intake, pre-qual, document checklists, lender pipeline | buy-this, idd-lender-package |
| Legal Document Review | Reviews purchase agreements, seller-finance notes, master leases, JV docs before they go to counsel | master-lease, oc-cowholesale-jv, buy-this |
| Grant Writer | LOIs, full proposals, budget narratives for Chafee, HUD, state DD grants | grant-dispatcher, foster-youth-scout |
| ZK Steward | Zettelkasten discipline for the olympus-vault second brain | learn, import-memory, syncer |

Runners-up worth adding later: Chief Financial Officer, Real Estate Buyer & Seller, Business Strategist, Document Generator, Workflow Architect.

### Marketing (5 of 36)
| Agent | Why it helps | Pairs with |
|---|---|---|
| Content Creator | Editorial calendar and repurposing across every platform | distribute, content-atomizer |
| LinkedIn Content Creator | Thought leadership for JV partners, lenders, and referral sources | distribute |
| Video Optimization Specialist | YouTube titles, chapters, thumbnails, retention | distribute, youtube-transcript |
| Email Marketing Strategist | Lifecycle sequences and segmentation inside Go High Level | apollo, the-follow-up-machine |
| Short-Video Editing Coach | Post-production for the video inbox before distribution | distribute |

### Sales (5 of 9)
| Agent | Why it helps | Pairs with |
|---|---|---|
| Outbound Strategist | ICPs and multi-channel sequences for motivated sellers and referral partners | artemis, apollo |
| Offer & Lead Gen Strategist | Irresistible offers and lead magnets | lead-magnet-builder, oc-dta-outreach |
| Pipeline Analyst | Stale-deal diagnostics, velocity, forecast accuracy | apollo, marketing-scorecard |
| Proposal Strategist | Win narratives for JV, lender, and operator proposals | idd-pitch, alf-jv-deal-review |
| Discovery Coach | Question design for seller and case-worker calls | oc-deal-qualifier, apollo |

### Finance (all 5)
Bookkeeper & Controller, Financial Analyst, FP&A Analyst, Investment Researcher, Tax Strategist. Every one maps to an operating company that holds real estate and runs licensed care homes. Pairs with operating-model, every underwriter skill, and maximizer-exit.

### Product (all 5)
Product Manager, Sprint Prioritizer, Feedback Synthesizer, Trend Researcher, Behavioral Nudge Engine. Use them to run the skill stack itself like a product: roadmap, prioritization, and pattern-finding across feedback from partners and residents. Pairs with take-a-step-back, brain-dump, bull-bear.

### Project Management (5 of 7)
| Agent | Why it helps | Pairs with |
|---|---|---|
| Senior Project Manager | Specs to tasks with realistic scope and memory of past projects | zeus, eos-strety |
| Meeting Notes Specialist | Decisions, actions, and open questions from Granola, Plaud, and Zoom transcripts | last-30-days, morning |
| Project Shepherd | Cross-functional timelines for a property going from offer to licensed and occupied | master-lease, rtc-feasibility |
| Studio Operations | Day-to-day process and resource coordination | operating-model |
| Experiment Tracker | Tracks outreach and marketing experiments to a decision | marketing-scorecard, the-upsell-finder |

### Support (5 of 6)
| Agent | Why it helps | Pairs with |
|---|---|---|
| Executive Summary Generator | Consultant-grade one-pagers for investors | alf-jv-deal-review, idd-pitch |
| Analytics Reporter | Dashboards and statistics on pipeline and portfolio data | token-dashboard, marketing-scorecard |
| Finance Tracker | Budget versus actual on each home | operating-model |
| Legal Compliance Checker | Fair-housing, licensing, and marketing-claim checks | sober-living, alf-senior, idd |
| Support Responder | Resident, family, and case-worker inquiry handling | hermes |

### Security (5 of 12)
| Agent | Why it helps | Pairs with |
|---|---|---|
| AI-Generated Code Security Auditor | Catches leaked keys and broken row-level security in vibe-coded landing pages and Supabase apps | landing-page, web-artifacts-builder |
| Secrets & Credential Hygiene Engineer | Rotation and leak response for GHL, Supabase, Vercel, and API keys | clone-my-setup, mcp-builder |
| Compliance Auditor | HIPAA readiness for homes handling resident health records | idd, alf-senior, rtc-feasibility |
| Senior SecOps Engineer | Scans commits for secrets before push | every skill that writes code |
| Security Architect | Trust boundaries for the multi-agent and MCP setup | mcp-builder, syncer |

### Testing (5 of 9)
| Agent | Why it helps | Pairs with |
|---|---|---|
| Reality Checker | Defaults to NEEDS WORK; demands evidence before anything is called done | aletheia, gospel-review |
| Evidence Collector | Screenshot-backed QA for browser automations | artemis, apollo |
| Workflow Optimizer | Finds and automates repeat work across skills | the-fire-yourself-skill, dbs-framework |
| Tool Evaluator | Structured comparison before adopting a new SaaS or MCP | steal-their-strategy |
| Test Automation Engineer | Resilient Playwright selectors for DealSauce and GHL flows | artemis, apollo |

### Design (5 of 10)
| Agent | Why it helps | Pairs with |
|---|---|---|
| Brand Guardian | Consistency across P.A.T.H. materials and the calm-teacher voice | distribute, landing-page |
| Persona Walkthrough Specialist | Simulates a seller, a lender, or a case worker scrolling a page | landing-page, lead-magnet-builder |
| Image Prompt Engineer | Thumbnails and visuals via Higgsfield and Magica | distribute, lesson-infographic |
| Visual Storyteller | Visual narratives for pitches and infographics | lesson-infographic, idd-pitch |
| UI Designer | Cleaner report and dashboard layouts | web-artifacts-builder |

Runner-up: Inclusive Visuals Specialist, for authentic imagery of the residents you serve.

### Paid Media (5 of 7)
Paid Media Auditor, Ad Creative Strategist, Paid Social Strategist, Tracking & Measurement Specialist, PPC Campaign Strategist. For when seller-lead or operator-recruitment campaigns go paid. Pairs with marketing-scorecard and seo-quick-audit.

### Research (1 of 1)
Research Synthesist. Turns a pile of sources into a defensible synthesis. Pairs with perplexity-research, bull-bear, and aletheia.

### Healthcare (all 3)
Clinical Evidence Agent, Healthcare Innovation Strategist, Sovereign Health Systems Agent. Evidence standards and narrative for Medicaid-waiver and licensed-care conversations. Pairs with idd-pitch, alf-neuro, and rtc-feasibility.

### Academic (4 of 6)
Statistician (pressure-tests numeric claims), Psychologist (seller and resident motivation), Geographer (market selection), Narratologist (story structure for content). Historian and Anthropologist skipped as worldbuilding tools.

### GIS (3 of 13)
GIS Analyst, Spatial Data Scientist, Web GIS Developer. Market maps of demand, competitors, and zoning for aged-out-market and the feasibility skills. The other ten are drone, BIM, and 3D tooling.

### Skipped divisions
Game Development and Spatial Computing have no fit. Integrations is upstream tooling docs.

## Reference material (not agents)

`reference/strategy/` holds the NEXUS orchestration doctrine from upstream: the master strategy, quick start, executive brief, handoff templates, and activation prompts. The Reality Checker gate and the handoff templates are the closest analog to the aletheia and devils-advocate gates and are worth mining when tightening those pipelines.

`reference/examples/` holds two upstream workflows: one with cross-session memory, one for a landing page.

## Refreshing from upstream

```bash
git clone --depth 1 https://github.com/msitarzewski/agency-agents /tmp/aa
cp /tmp/aa/finance/*.md .claude/agents/     # or any file listed above
```
