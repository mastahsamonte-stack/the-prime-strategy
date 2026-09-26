# Prime Command Center

You give an order, the agents do the job, and you watch it happen from any browser, including your phone.

```
Your order ──► Research Agent ──► picks the skill ──► finds or creates the vault folder ──► runs the skill ──► files the report
                                                                                                          │
Board (phone) ◄── every step is posted here ◄── Verdict Agent writes VERDICT.md: YES / MAYBE / NO ◄───────┘
```

| Piece | File | Job |
|---|---|---|
| Research Agent | `.claude/agents/prime-research-agent.md` | Picks the right skill from its routing table, resolves the topic folder, runs the skill, files the output |
| Verdict Agent | `.claude/agents/prime-verdict-agent.md` | Reads the report and gives the bottom line: YES (buy or invest), MAYBE (only if…), or NO (pass) |
| Dispatcher and ledger | `command-center/cc.py` | Runs the agents one after the other and records every step in `~/Cowork/olympus/command-center/jobs/` |
| Board | `command-center/board.html` | The web page: send an order, watch the agents, read verdicts, open reports |

## Where research lands

`cc.py topic` decides the folder the same way every time:

1. It searches the vault (up to 4 levels deep) for a folder with the topic's name, such as `IDD`. If it finds one, it uses it.
2. If there's no match, it creates `05 Knowledge/Research/<Topic>/`.
3. An address becomes a subfolder, for example `IDD/123 Main St, Columbus OH/`.

The Research Agent also writes `NOTES.md` in that folder, recording the order, the skill it used and its assumptions. The Verdict Agent writes `VERDICT.md` next to the report.

To change where new topics go, set `PRIME_RESEARCH_ROOT`. To point at a different vault, set `PRIME_VAULT`.

## Setup on the Mac Mini (one time)

```bash
cd ~/Cowork/the-prime-strategy && git pull
./scripts/standby.sh                      # installs the 2 new agents globally + refreshes Vader's plugin
./command-center/install-mac.sh           # starts the board now and after every reboot
```

The last line prints a link ending in `?t=...`. That's your private token. Open that link once on each device, and the page remembers it. You can print the token again anytime with `python3 command-center/cc.py token`.

### Open it on your phone

The board only listens on the Mac Mini itself. That's on purpose: it can start Claude jobs, so it shouldn't be open to the internet. To reach it from your phone:

1. Install **Tailscale** on the Mac Mini and your phone, and sign in to both with the same account. It's free for personal use.
2. On the Mac Mini, run: `tailscale serve --bg 8787`
3. On your phone, open `https://<mac-mini-name>.<your-tailnet>.ts.net/?t=<token>` (`tailscale serve status` shows the exact address).

Only devices signed in to your Tailscale account can open it.

## Skills the agents can use

Your skills live in your Claude account. The Claude desktop app keeps a local copy, but Claude Code (which runs the agents) only reads `~/.claude/skills`. `scripts/sync-skills.sh` bridges the two:

```bash
./scripts/sync-skills.sh           # preview: what it would add, refresh, or skip. Changes nothing.
./scripts/sync-skills.sh --apply   # copy them in (run once, and again when you add a new skill)
```

It never overwrites a skill it didn't put there. Before every job the dispatcher runs `--refresh`, which updates the skills you already approved so edits in the Claude app reach the agents, and never adds new ones. If a job stops with "Skill … is not installed", run the preview and `--apply`.

## Give orders

- **Board:** type in the box, or tap the microphone on your phone keyboard and speak. Then tap **Send order**.
- **Terminal:** `python3 command-center/cc.py dispatch "research IDD group homes in Ohio"` (add `--bg` to return right away).
- **Vader, including Telegram voice notes:** tell Vader once:
  > When I give you a research, feasibility, or "should I buy this" order, run `python3 ~/Cowork/the-prime-strategy/command-center/cc.py dispatch --bg "<my order>"` and reply with the job id. Don't do the research yourself.

### Bottom line on a report you already have

```bash
python3 command-center/cc.py verdict "path/to/report.html" "Should I buy this as an IDD home?" --topic IDD --sub "12 Oak St"
```

The report is copied into the vault topic folder (the original stays put), and the Verdict Agent writes `VERDICT.md` next to it. The job shows on the board like any other.

## Test it first

Before your first real order, give it a small one and watch every step:

```bash
python3 command-center/cc.py dispatch "ELI15 what an HCBS waiver is"
```

Then check that `05 Knowledge/Research/…` (or your existing matching folder) holds the output, and that the board shows each step.

## Permissions for unattended runs

Nobody is at the keyboard to click "allow", so jobs run with a fixed allowlist: reading and writing files, web search and fetch, skills, subagents, and `python3`/`mkdir`/`cp`/`ls` in the shell. If a job needs anything else, that tool is denied and the job says so on the board. The usual cases are Chrome for DealSauce or Go High Level, and email connectors. Widen it deliberately, for example:

```bash
export PRIME_CLAUDE_FLAGS="--permission-mode auto"
```

Never use `--dangerously-skip-permissions` for jobs started from your phone.

## Job states

| State | Meaning |
|---|---|
| queued | Order received |
| working | An agent is on it. The step line says what it's doing right now. |
| needs phil | Blocked on you, such as a login, a missing skill or a denied tool. The step says exactly what to do. |
| done | Filed, with a verdict if one was needed |
| failed | Something broke. Tap **Log** to see the last lines. |
