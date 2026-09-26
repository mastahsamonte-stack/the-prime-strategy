#!/usr/bin/env python3
"""Prime Command Center: job ledger, topic folders, dispatcher, and phone board.

One file, standard library only, so it runs on the Mac Mini with nothing to install.

  cc.py dispatch "research IDD group homes in Ohio"   # run a job now (add --bg to detach)
  cc.py serve                                         # start the board on http://127.0.0.1:8787
  cc.py topic "IDD" --sub "123 Main St, Columbus OH"  # find or create the vault folder
  cc.py job new|update|verdict|show|list ...          # what the agents call to report status

Paths (override with env vars):
  PRIME_VAULT          ~/Cowork/olympus-vault
  PRIME_RESEARCH_ROOT  $PRIME_VAULT/05 Knowledge/Research   (new topic folders go here)
  PRIME_CC_HOME        ~/Cowork/olympus/command-center      (jobs/, logs/, token)
  PRIME_CLAUDE         claude                               (the Claude Code binary)
  PRIME_CLAUDE_FLAGS   permission flags for unattended runs (see DEFAULT_CLAUDE_FLAGS)
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import secrets
import shlex
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
VAULT = Path(os.environ.get("PRIME_VAULT", "~/Cowork/olympus-vault")).expanduser()
RESEARCH_ROOT = Path(os.environ.get("PRIME_RESEARCH_ROOT", str(VAULT / "05 Knowledge" / "Research"))).expanduser()
CC_HOME = Path(os.environ.get("PRIME_CC_HOME", "~/Cowork/olympus/command-center")).expanduser()
JOBS = CC_HOME / "jobs"
LOGS = CC_HOME / "logs"
CLAUDE = os.environ.get("PRIME_CLAUDE", "claude")
# Unattended runs cannot answer permission prompts, so anything not allowed here is
# denied and the agent reports it. Widen deliberately, e.g. PRIME_CLAUDE_FLAGS="--permission-mode auto".
DEFAULT_CLAUDE_FLAGS = (
    "--permission-mode acceptEdits --allowedTools "
    "Read Write Edit Glob Grep WebSearch WebFetch Skill Agent Task TodoWrite "
    "'Bash(python3:*)' 'Bash(mkdir:*)' 'Bash(cp:*)' 'Bash(ls:*)'"
)
CLAUDE_FLAGS = os.environ.get("PRIME_CLAUDE_FLAGS", DEFAULT_CLAUDE_FLAGS)

STATUSES = ("queued", "working", "needs-phil", "done", "failed")
CALLS = ("YES", "MAYBE", "NO")
AGENTS = {
    "prime-research-agent": {"label": "Research Agent", "emoji": "🔎"},
    "prime-verdict-agent": {"label": "Verdict Agent", "emoji": "⚖️"},
}
SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules", "__pycache__"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- job ledger

def _job_path(job_id: str) -> Path:
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[a-z0-9]{4}", job_id or ""):
        raise SystemExit(f"bad job id: {job_id!r}")
    return JOBS / f"{job_id}.json"


def load_job(job_id: str) -> dict:
    return json.loads(_job_path(job_id).read_text())


def save_job(job: dict) -> dict:
    JOBS.mkdir(parents=True, exist_ok=True)
    job["updated"] = now()
    path = _job_path(job["id"])
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(job, indent=2))
    tmp.replace(path)  # atomic, so the board never reads half a file
    return job


def new_job(order: str, agent: str = "prime-research-agent") -> dict:
    job_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2)
    job = {
        "id": job_id, "order": order.strip(), "status": "queued", "agent": agent,
        "step": "Waiting for an agent", "skill": None, "topic": None, "folder": None,
        "report": None, "needs_verdict": None, "verdict": None,
        "history": [], "created": now(),
    }
    return save_job(job)


def update_job(job_id: str, **fields) -> dict:
    job = load_job(job_id)
    for key, value in fields.items():
        if value is None:
            continue
        if key == "status" and value not in STATUSES:
            raise SystemExit(f"status must be one of {STATUSES}")
        job[key] = value
    note = fields.get("step")
    if note:
        job["history"].append({"at": now(), "agent": job.get("agent"), "step": note})
        job["history"] = job["history"][-50:]
    return save_job(job)


def list_jobs(limit: int = 50) -> list[dict]:
    if not JOBS.exists():
        return []
    jobs = []
    for p in sorted(JOBS.glob("*.json"), reverse=True)[:limit]:
        try:
            jobs.append(json.loads(p.read_text()))
        except (OSError, json.JSONDecodeError):
            continue
    return jobs


# ------------------------------------------------------------- topic folders

def _norm(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _safe_name(text: str) -> str:
    name = re.sub(r'[\\/:*?"<>|#^\[\]]+', " ", text).strip().strip(".")
    return re.sub(r"\s+", " ", name)[:80] or "Untitled"


def find_topic_folders(topic: str, max_depth: int = 4) -> list[Path]:
    """Folders anywhere in the vault whose name matches the topic (ignoring case/punctuation)."""
    want = _norm(topic)
    hits: list[Path] = []
    if not want or not VAULT.exists():
        return hits
    for root, dirs, _ in os.walk(VAULT):
        depth = len(Path(root).relative_to(VAULT).parts)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        if depth >= max_depth:
            dirs[:] = []
        for d in dirs:
            if _norm(d) == want:
                hits.append(Path(root) / d)
    # Prefer the research root, then the shallowest path, so the choice is stable.
    return sorted(hits, key=lambda p: (RESEARCH_ROOT not in p.parents, len(p.parts), str(p)))


def resolve_topic(topic: str, sub: str | None = None, create: bool = True) -> dict:
    hits = find_topic_folders(topic)
    created = False
    folder = hits[0] if hits else RESEARCH_ROOT / _safe_name(topic)
    if sub:
        folder = folder / _safe_name(sub)
    if not folder.exists() and create:
        folder.mkdir(parents=True, exist_ok=True)
        created = True
    return {"topic": topic, "folder": str(folder), "created": created,
            "existing_matches": [str(p) for p in hits]}


# ---------------------------------------------------------------- dispatcher

def _claude(agent: str, prompt: str, log: Path) -> int:
    # Run from the repo so the prime- agents load even if standby.sh hasn't installed
    # them globally; --add-dir gives the job the vault.
    VAULT.mkdir(parents=True, exist_ok=True)
    cmd = [CLAUDE, "-p", "--agent", agent, "--add-dir", str(VAULT), *shlex.split(CLAUDE_FLAGS)]
    with log.open("a") as out:
        out.write(f"\n===== {now()} {agent}\n")
        out.flush()
        # The prompt goes in on stdin: --allowedTools is variadic and would swallow a trailing argument.
        proc = subprocess.run(cmd, cwd=HERE.parent, input=prompt, text=True,
                              stdout=out, stderr=subprocess.STDOUT)
    return proc.returncode


def _tail(path: Path, lines: int = 12) -> str:
    try:
        return "\n".join(path.read_text(errors="replace").splitlines()[-lines:])
    except OSError:
        return ""


def run_job(job_id: str) -> dict:
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f"{job_id}.log"
    cc = f"python3 {shlex.quote(str(Path(__file__).resolve()))}"
    # Pick up Phil's latest edits to skills he already approved; never installs new ones.
    sync = HERE.parent / "scripts" / "sync-skills.sh"
    if sync.exists():
        with log.open("a") as out:
            subprocess.run([str(sync), "--refresh"], stdout=out, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL)
    job = update_job(job_id, status="working", agent="prime-research-agent",
                     step="Research Agent picked up the order")
    brief = (
        f"JOB_ID: {job_id}\nCC: {cc}\n\nOrder from Phil:\n{job['order']}\n\n"
        "Follow your job protocol: choose the skill, resolve the topic folder with CC, "
        "report every step with CC, and finish with CC job update --status done."
    )
    code = _claude("prime-research-agent", brief, log)
    job = load_job(job_id)
    if code != 0 and job["status"] != "done":
        return update_job(job_id, status="failed",
                          step=f"Research Agent exited with code {code}. Last log lines:\n{_tail(log)}")
    if job["status"] == "working":
        job = update_job(job_id, status="failed",
                         step="Research Agent stopped without reporting done. Check the log.")
    if job["status"] != "done" or not job.get("report"):
        return job
    if job.get("needs_verdict") is False:
        return job

    update_job(job_id, status="working", agent="prime-verdict-agent",
               step="Verdict Agent is reading the report")
    brief = (
        f"JOB_ID: {job_id}\nCC: {cc}\n\nOriginal order: {job['order']}\n"
        f"Report: {job['report']}\nFolder: {job['folder']}\n\n"
        "Write VERDICT.md in the folder, record it with CC job verdict, "
        "then CC job update --status done."
    )
    code = _claude("prime-verdict-agent", brief, log)
    job = load_job(job_id)
    if job["status"] == "needs-phil":
        return job
    if not job.get("verdict"):
        return update_job(job_id, status="failed",
                          step=f"Verdict Agent finished without a verdict (exit {code}). Check the log.")
    if job["status"] == "working":
        job = update_job(job_id, status="done", step="Verdict delivered")
    return job


def dispatch(order: str, background: bool) -> dict:
    job = new_job(order)
    if background:
        LOGS.mkdir(parents=True, exist_ok=True)
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "run", job["id"]],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=(LOGS / f"{job['id']}.runner.log").open("a"),
                         start_new_session=True)
        return job
    return run_job(job["id"])


# --------------------------------------------------------------------- board

def _token() -> str:
    CC_HOME.mkdir(parents=True, exist_ok=True)
    path = CC_HOME / "token"
    if not path.exists():
        path.write_text(secrets.token_urlsafe(24))
        path.chmod(0o600)
    return path.read_text().strip()


def _inside_vault(p: str | None) -> Path | None:
    if not p:
        return None
    path = Path(p).expanduser().resolve()
    vault = VAULT.resolve()
    return path if path.is_file() and (path == vault or vault in path.parents) else None


class Board(BaseHTTPRequestHandler):
    token = ""

    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass

    def _authed(self, query: dict) -> bool:
        given = self.headers.get("X-Prime-Token") or (query.get("t") or [""])[0]
        return hmac.compare_digest(given.encode(), self.token.encode())

    def _send(self, code: int, body: bytes, ctype: str, sandbox: bool = False) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if sandbox:  # vault files render in an opaque origin, away from the board's token
            self.send_header("Content-Security-Policy", "sandbox")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, data) -> None:
        self._send(code, json.dumps(data).encode(), "application/json")

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path in ("/", "/index.html"):
            return self._send(200, (HERE / "board.html").read_bytes(), "text/html; charset=utf-8")
        if not self._authed(query):
            return self._json(401, {"error": "token required"})
        if url.path == "/api/jobs":
            return self._json(200, {"jobs": list_jobs(), "agents": AGENTS, "vault": str(VAULT)})
        m = re.fullmatch(r"/api/jobs/([0-9a-z-]+)/(report|verdict|log)", url.path)
        if m:
            job_id, which = m.groups()
            try:
                job = load_job(job_id)
            except (SystemExit, OSError):
                return self._json(404, {"error": "no such job"})
            if which == "log":
                return self._send(200, _tail(LOGS / f"{job_id}.log", 200).encode(), "text/plain; charset=utf-8")
            target = job.get("report") if which == "report" else (job.get("verdict") or {}).get("file")
            path = _inside_vault(target)
            if not path:
                return self._json(404, {"error": f"{which} not found inside the vault"})
            ctype = "text/html; charset=utf-8" if path.suffix.lower() in (".html", ".htm") else "text/plain; charset=utf-8"
            if path.suffix.lower() == ".pdf":
                ctype = "application/pdf"
            return self._send(200, path.read_bytes(), ctype, sandbox=True)
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        url = urlparse(self.path)
        if not self._authed(parse_qs(url.query)):
            return self._json(401, {"error": "token required"})
        if url.path != "/api/dispatch":
            return self._json(404, {"error": "not found"})
        length = min(int(self.headers.get("Content-Length") or 0), 20_000)
        try:
            order = str(json.loads(self.rfile.read(length) or b"{}").get("order", "")).strip()
        except json.JSONDecodeError:
            order = ""
        if not order:
            return self._json(400, {"error": "order is empty"})
        return self._json(202, dispatch(order, background=True))


def serve(host: str, port: int) -> None:
    Board.token = _token()
    server = ThreadingHTTPServer((host, port), Board)
    print(f"Prime Command Center board: http://{host}:{port}/?t={Board.token}")
    print("Open that link once on each device; the page remembers the token.")
    print(f"Jobs: {JOBS}   Vault: {VAULT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


# ----------------------------------------------------------------------- cli

def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dispatch", help="create a job and run the agents on it")
    d.add_argument("order", nargs="+")
    d.add_argument("--bg", action="store_true", help="return immediately; the job runs in the background")
    r = sub.add_parser("run", help="run an existing queued job")
    r.add_argument("job_id")

    s = sub.add_parser("serve", help="start the web board")
    s.add_argument("--host", default=os.environ.get("PRIME_CC_HOST", "127.0.0.1"))
    s.add_argument("--port", type=int, default=int(os.environ.get("PRIME_CC_PORT", "8787")))
    sub.add_parser("token", help="print the board token")

    t = sub.add_parser("topic", help="find the vault folder for a topic, creating it if missing")
    t.add_argument("topic")
    t.add_argument("--sub", help="subfolder, e.g. a property address")
    t.add_argument("--no-create", action="store_true")
    t.add_argument("--job", help="also record topic and folder on this job")

    j = sub.add_parser("job", help="ledger operations the agents call")
    jsub = j.add_subparsers(dest="op", required=True)
    jn = jsub.add_parser("new"); jn.add_argument("order"); jn.add_argument("--agent", default="prime-research-agent")
    ju = jsub.add_parser("update"); ju.add_argument("job_id")
    ju.add_argument("--status", choices=STATUSES); ju.add_argument("--step"); ju.add_argument("--skill")
    ju.add_argument("--report"); ju.add_argument("--folder"); ju.add_argument("--agent")
    ju.add_argument("--needs-verdict", choices=("yes", "no"))
    jv = jsub.add_parser("verdict"); jv.add_argument("job_id")
    jv.add_argument("--call", required=True, choices=CALLS)
    jv.add_argument("--confidence", required=True, choices=("high", "medium", "low"))
    jv.add_argument("--line", required=True, help="one plain-English sentence")
    jv.add_argument("--file", required=True, help="path to VERDICT.md")
    js = jsub.add_parser("show"); js.add_argument("job_id")
    jsub.add_parser("list")

    a = ap.parse_args(argv)
    out = None
    if a.cmd == "dispatch":
        out = dispatch(" ".join(a.order), a.bg)
    elif a.cmd == "run":
        out = run_job(a.job_id)
    elif a.cmd == "serve":
        return serve(a.host, a.port)
    elif a.cmd == "token":
        return print(_token())
    elif a.cmd == "topic":
        out = resolve_topic(a.topic, a.sub, create=not a.no_create)
        if a.job:
            update_job(a.job, topic=a.topic, folder=out["folder"],
                       step=f"Filing into {out['folder']}" + (" (new folder)" if out["created"] else ""))
    elif a.op == "new":
        out = new_job(a.order, a.agent)
    elif a.op == "update":
        nv = None if a.needs_verdict is None else a.needs_verdict == "yes"
        out = update_job(a.job_id, status=a.status, step=a.step, skill=a.skill,
                         report=a.report, folder=a.folder, agent=a.agent, needs_verdict=nv)
    elif a.op == "verdict":
        verdict = {"call": a.call, "confidence": a.confidence, "line": a.line,
                   "file": str(Path(a.file).expanduser())}
        out = update_job(a.job_id, verdict=verdict, step=f"Verdict: {a.call} ({a.confidence}) - {a.line}")
    elif a.op == "show":
        out = load_job(a.job_id)
    elif a.op == "list":
        out = [{k: j.get(k) for k in ("id", "status", "agent", "step", "order")} for j in list_jobs()]
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
