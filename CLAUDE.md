# The Prime Strategy

This repo is the curated specialist roster for Phil's operating system. It is orchestrated by **Vader**, a Hermes Agent running on Phil's Mac. Vader launches jobs and skills through Phil's Claude subscription. Claude sessions started by Vader are workers, not the orchestrator.

## Roster

- `.claude/agents/` holds 71 agent personas (verbatim from msitarzewski/agency-agents, MIT). Inside this repo they load automatically as project subagents. On Phil's Mac they are also installed globally by `scripts/standby.sh`, so any Claude Code job Vader launches, in any directory, can use them.
- `integrations/hermes/agency-agents-router/` is the same roster packaged as a Hermes plugin so Vader can search, inspect, load, or delegate to a specialist lazily.
- `README.md` maps every agent to the Phil skill it supports. Read it before choosing an agent.

## Working rules for a Claude session in this repo

- Prefer Phil's existing skills (deal-analyzer, aged-out-sil, alf-senior, artemis, apollo, council, aletheia, and so on) for procedure. Use these agents as personas inside those procedures, never as a replacement for them.
- Load only the specialists a task needs. Never preload the whole roster.
- Do not edit agent files in place to customize them. Copy to a new file with a `prime-` prefix so upstream refreshes stay clean.
- After adding or removing any file in `.claude/agents/`, run `./scripts/build-hermes.sh` and commit the regenerated `integrations/hermes/` output.
- Vault captures follow `~/Cowork/olympus/AI_SYNC_PROTOCOL.md` when that path exists. Draft only; never install skills or update memory without Phil's approval.
