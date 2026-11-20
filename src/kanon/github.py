"""GitHub mode (P1-10): Kanon acts on GitHub only as its own GitHub App, never as a person.

The App's ID and slug live in `[github]` of `kanon/kanon.toml`. Its private key lives outside every
repository: `KANON_APP_KEY` (PEM, or base64 of the PEM) in cloud environments, or
`~/.config/kanon/github-app.pem` on a person's computer. A 10-minute JWT signed with the key buys
a 1-hour installation token limited to this repository; tokens are kept in memory only. Every
call runs locally, so no GitHub Actions minutes are used (ADR-007).
"""

from __future__ import annotations

import base64
import json
import os
import re
import ssl
import subprocess
import time
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

API = os.environ.get("KANON_GITHUB_API", "https://api.github.com")
PERMISSIONS = {"contents": "write", "pull_requests": "write", "metadata": "read"}
MARKER = "<!-- kanon:pull-request -->"


class GitHubError(RuntimeError):
    pass


# ---------------------------------------------------------------- key, settings and identity

def key_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "kanon" / "github-app.pem"


def load_key() -> bytes:
    """The App's private key as PEM bytes. Never printed or written by Kanon outside key_path()."""
    inline = os.environ.get("KANON_APP_KEY", "").strip()
    if inline:
        if "BEGIN" in inline:
            return (inline.replace("\\n", "\n") + "\n").encode()
        try:
            decoded = base64.b64decode(inline, validate=True)
        except ValueError:
            raise GitHubError("KANON_APP_KEY is neither a PEM key nor base64 of one") from None
        if b"BEGIN" not in decoded:
            raise GitHubError("KANON_APP_KEY is neither a PEM key nor base64 of one")
        return decoded
    path = Path(os.environ.get("KANON_APP_KEY_FILE") or key_path())
    if path.is_file():
        return path.read_bytes()
    raise GitHubError("no App key: set KANON_APP_KEY in the environment, or run kanon github setup on your computer")


def settings(root: Path) -> dict:
    try:
        data = tomllib.loads((root / "kanon" / "kanon.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    section = data.get("github", {})
    return section if isinstance(section, dict) else {}


def app_id(root: Path) -> str:
    value = str(settings(root).get("app_id") or os.environ.get("KANON_APP_ID", "")).strip()
    if not value:
        raise GitHubError("no App ID: add app_id to [github] in kanon/kanon.toml (or KANON_APP_ID)")
    return value


def repository(root: Path) -> str:
    """owner/name of the repository's GitHub remote."""
    url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, capture_output=True, text=True).stdout.strip()
    match = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?/?$", url) or \
        re.search(r"/git/([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if not match:
        raise GitHubError(f"the origin remote is not a GitHub repository ({url or 'none'})")
    return f"{match.group(1)}/{match.group(2)}"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_jwt(issuer: str, key_pem: bytes, now: int | None = None) -> str:
    """An RS256 JWT for the App, valid for 9 minutes (GitHub allows 10)."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    now = int(time.time()) if now is None else now
    header = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode())
    claims = _b64(json.dumps({"iat": now - 60, "exp": now + 540, "iss": issuer}, separators=(",", ":")).encode())
    try:
        key = serialization.load_pem_private_key(key_pem, password=None)
    except (ValueError, TypeError):
        raise GitHubError("the App key is not a valid RSA private key") from None  # K-414
    signature = key.sign(f"{header}.{claims}".encode(), padding.PKCS1v15(), hashes.SHA256())
    return f"{header}.{claims}.{_b64(signature)}"


# ---------------------------------------------------------------- HTTP

def _context() -> ssl.SSLContext:
    bundle = next((os.environ[v] for v in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE")
                   if os.environ.get(v) and Path(os.environ[v]).is_file()), None)
    return ssl.create_default_context(cafile=bundle)


def call(method: str, path: str, token: str | None = None, body: dict | None = None, kind: str = "token"):
    """One GitHub API call. Returns the decoded JSON (or None). Raises GitHubError with GitHub's message."""
    request = urllib.request.Request(API + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("User-Agent", "kanon-engine")
    if token:
        request.add_header("Authorization", f"{'Bearer' if kind == 'jwt' else 'token'} {token}")
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, context=_context(), timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        try:
            detail = json.loads(detail).get("message", detail)
        except (ValueError, AttributeError):
            pass
        raise GitHubError(f"GitHub {method} {path}: {error.code} {detail}") from None
    except urllib.error.URLError as error:
        raise GitHubError(f"GitHub could not be reached: {error.reason}") from None
    return json.loads(raw) if raw else None


@dataclass
class Session:
    """The App signed in for one repository."""
    repo: str
    token: str = field(repr=False)  # never shown (K-410)
    installation: dict = field(default_factory=dict)
    app: dict = field(default_factory=dict)
    granted: dict = field(default_factory=dict)


def sign_in(root: Path) -> Session:
    issuer, key = app_id(root), load_key()
    repo = repository(root)
    jwt = make_jwt(issuer, key)
    app = call("GET", "/app", jwt, kind="jwt")
    installation = call("GET", f"/repos/{repo}/installation", jwt, kind="jwt")
    wanted = {k: v for k, v in PERMISSIONS.items() if k in (installation.get("permissions") or {})}
    grant = call("POST", f"/app/installations/{installation['id']}/access_tokens", jwt,
                 {"repositories": [repo.split("/", 1)[1]], "permissions": wanted}, kind="jwt")
    return Session(repo, grant["token"], installation, app, grant.get("permissions") or {})


def check(root: Path) -> list[str]:
    """Lines describing the App's set-up, for `kanon github check`. Raises GitHubError when it fails."""
    session = sign_in(root)
    lines = [f"App: {session.app.get('name')} ({session.app.get('slug')}), ID {session.app.get('id')}",
             f"Installed on: {session.repo} (installation {session.installation.get('id')}, "
             f"{session.installation.get('repository_selection')} repositories)",
             "Token permissions: " + ", ".join(f"{k}: {v}" for k, v in sorted(session.granted.items()))]
    missing = [k for k, v in PERMISSIONS.items() if session.granted.get(k) not in (v, "write")]
    extra = sorted(set(session.installation.get("permissions") or {}) - set(PERMISSIONS))
    if missing:
        lines.append("Missing permissions: " + ", ".join(missing))
    if "administration" in (session.installation.get("permissions") or {}):
        lines.append("Warning: the App has the Administration permission; remove it so it cannot change branch protection")
    if extra:
        lines.append("Other permissions (not used by Kanon): " + ", ".join(extra))
    configured = settings(root)
    if str(configured.get("app_id", "")) != str(session.app.get("id")) or configured.get("app_slug") != session.app.get("slug"):
        lines += ["Add these lines to kanon/kanon.toml:", "", "[github]", f"app_id = {session.app.get('id')}",
                  f'app_slug = "{session.app.get("slug")}"']  # K-411
    return lines


# ---------------------------------------------------------------- push and pull requests

def push(root: Path, session: Session, branch: str) -> None:
    """Push a branch with the App's token; never forces.

    The person's own Git configuration is ignored, so an `insteadOf` rule cannot send the push over
    SSH as the person (K-406); the token travels in the environment, not the command line (K-410).
    """
    if not re.fullmatch(r"kanon/[A-Za-z0-9._/-]+", branch):
        raise GitHubError(f"Kanon pushes only kanon/* branches, not {branch}")
    local = subprocess.run(["git", "config", "--local", "--get-regexp", r"^url\."], cwd=root, capture_output=True,
                           text=True).stdout.strip()
    if local:
        raise GitHubError("this repository's Git configuration rewrites URLs (url.*.insteadOf); remove it so the push "
                          "goes as the App, not as you")
    header = base64.b64encode(f"x-access-token:{session.token}".encode()).decode()
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
           "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "http.https://github.com/.extraHeader",
           "GIT_CONFIG_VALUE_0": f"Authorization: Basic {header}", "GIT_CONFIG_KEY_1": "credential.helper",
           "GIT_CONFIG_VALUE_1": ""}
    url = f"https://github.com/{session.repo}.git"
    result = subprocess.run(["git", "push", url, f"refs/heads/{branch}:refs/heads/{branch}"],
                            cwd=root, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        message = result.stderr.replace(session.token, "***").replace(header, "***").strip()
        raise GitHubError(f"push of {branch} failed: {message}")


def _pull_for(session: Session, head: str, base: str) -> dict | None:
    owner = session.repo.split("/")[0]
    found = call("GET", f"/repos/{session.repo}/pulls?state=open&head={owner}:{head}&base={base}", session.token)
    return found[0] if found else None


def open_or_update(session: Session, head: str, base: str, title: str, body: str) -> dict:
    existing = _pull_for(session, head, base)
    if existing:
        return call("PATCH", f"/repos/{session.repo}/pulls/{existing['number']}", session.token,
                    {"title": title, "body": body})
    return call("POST", f"/repos/{session.repo}/pulls", session.token,
                {"title": title, "head": head, "base": base, "body": body, "maintainer_can_modify": False})


def comment_review(session: Session, number: int, body: str) -> dict:
    """Reviewer notes as a comment-only review. Kanon never submits APPROVE or REQUEST_CHANGES."""
    return call("POST", f"/repos/{session.repo}/pulls/{number}/reviews", session.token, {"event": "COMMENT", "body": body})


def reviews(session: Session, number: int) -> list[dict]:
    return call("GET", f"/repos/{session.repo}/pulls/{number}/reviews?per_page=100", session.token) or []


# ---------------------------------------------------------------- description, without a model

def _section(text: str, name: str) -> list[str]:
    lines, out, inside = text.split("\n"), [], False
    for line in lines:
        if line.startswith("## "):
            inside = re.sub(r"^## (?:\d+\.\s+)?", "", line).strip() == name
            continue
        if inside:
            out.append(line)
    return out


def describe(root: Path, work_rel: str, text: str, plan_branch: str, base: str = "main") -> str:
    """The pull request description: items with their merge commits, review rounds and cost."""
    from kanon import branch as branches
    title = next((l[2:].strip() for l in text.split("\n") if l.startswith("# ")), work_rel)
    summary = " ".join(l[2:].replace("**Summary:**", "").strip() for l in text.split("\n")
                       if l.startswith("> **Summary:**"))
    work = branches.re.sub(r"^\d{4}-\d{2}-\d{2}-", "", Path(work_rel).stem)
    merges = subprocess.run(["git", "log", "--merges", "--format=%h %s", f"{base}..{plan_branch}"], cwd=root,
                            capture_output=True, text=True).stdout.splitlines()
    out = [MARKER, f"## {title}", "", summary, "", f"Work file: `{work_rel}`", "", "### Items", "",
           "| Item | Merge commit | Review |", "|---|---|---|"]
    for item in branches.items(text):
        merge = next((m.split()[0] for m in merges if re.search(rf"merge {re.escape(item)} into", m)), "not merged")
        out.append(f"| {item} | {merge} | {branches.review_state(text, item)[1]} |")
    review = [l for l in _section(text, "Review") if l.startswith("|")]
    cost = [l for l in _section(text, "Cost") if l.startswith("|")]
    out += ["", "### Review Rounds", "", *(review or ["Not yet reviewed."]), "", "### Cost", "",
            *(cost or ["Not recorded."]), "",
            f"Generated by `kanon github pr {work}` from the work file, without a model call. "
            "Merging this pull request is the approval (a code owner's review is required)."]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- approvals read back

def approvals(review_list: list[dict], approvers: list[str], head_sha: str) -> list[dict]:
    """Reviews that decide: the latest by each listed approver, on the pull request's head commit."""
    allowed = {a.lower() for a in approvers}
    latest: dict[str, dict] = {}
    for review in review_list:
        user = (review.get("user") or {}).get("login", "")
        if user.lower() in allowed and review.get("state") in ("APPROVED", "CHANGES_REQUESTED"):
            latest[user.lower()] = review
    return [r for r in latest.values() if r.get("commit_id") == head_sha]


# ---------------------------------------------------------------- commands

CACHE = "kanon/local/pull-requests.json"
ON_MERGE = "Approved on merge of pull request"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if result.returncode != 0:
        raise GitHubError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def read_cache(root: Path) -> dict:
    try:
        data = json.loads((root / CACHE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_cache(root: Path, data: dict) -> None:
    path = root / CACHE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mark_on_merge(text: str, number: int, url: str, today: str, merged_items: list[str]) -> str:
    """Record that the pull request's merge is the approval (owner, 2026-11-20).

    The work stays `awaiting-approval` until the merge: the Desk and `kanon verify` read the merge
    commit from Git history (K-400, K-402). A fresh row is added after a change request (K-403).
    """
    from kanon import approve
    rows_now = approve.decision_rows(text)
    if rows_now and f"{ON_MERGE} #{number}" in rows_now[-1].decision:
        return text
    rows = [f"| {item} | {ON_MERGE} #{number} | {today} | {url}; a code owner's review is required to merge |"
            for item in merged_items] or \
           [f"| Result | {ON_MERGE} #{number} | {today} | {url}; a code owner's review is required to merge |"]
    head, lines = approve._split(text)
    for row in rows:
        approve._append_row(lines, row)
    if not merged_items:  # a single-item work file: the merge of this pull request decides it
        head = re.sub(r"^status: .*$", "status: awaiting-approval", head, count=1, flags=re.M)
        _decision_needed(lines, f"Review and merge pull request #{number} on GitHub; the merge is the approval.")
    return head + "\n".join(lines)


def _decision_needed(lines: list[str], text: str) -> None:
    for index, line in enumerate(lines):
        if line.startswith("> **Decision needed:**") or line.startswith("> **Decision:**"):
            end = index + 1
            while end < len(lines) and lines[end].startswith(">") and not lines[end].startswith("> **"):
                end += 1
            lines[index:end] = [f"> **Decision needed:** {text}"]
            return


def _mark_closed(text: str, number: int, url: str, today: str) -> str:
    """A pull request closed without merging reopens the work (K-401)."""
    from kanon import approve
    if f"Pull request #{number} closed without merging" in text:
        return text
    head, lines = approve._split(text)
    approve._append_row(lines, f"| Result | Pull request #{number} closed without merging | {today} | {url} |")
    head = re.sub(r"^status: .*$", "status: in-progress", head, count=1, flags=re.M)
    _decision_needed(lines, f"None yet; pull request #{number} was closed without merging.")
    return head + "\n".join(lines)


def open_pull_request(root: Path, work: str, base: str = "main", session: Session | None = None,
                      today: str | None = None) -> dict:
    """Push the plan branch and open or update its pull request into base. Returns the pull request."""
    import datetime as dt
    from kanon import branch as branches
    plan = branches.plan_branch(work)
    if _git(root, "symbolic-ref", "--short", "HEAD") != plan:
        raise GitHubError(f"switch to {plan} first (kanon branch start {work})")
    if _git(root, "status", "--porcelain", "--untracked-files=no"):
        raise GitHubError("the working tree has uncommitted changes; commit them first")
    session = session or sign_in(root)
    rel, text = branches.work_file(root, work)
    title = next((l[2:].strip() for l in text.split("\n") if l.startswith("# ")), work)
    push(root, session, plan)
    pull = open_or_update(session, plan, base, title, describe(root, rel, text, plan, base))
    merged = [i for i in branches.items(text)
              if re.search(rf"merge {re.escape(i)} into", _git(root, "log", "--merges", "--format=%s", f"{base}..{plan}"))]
    marked = _mark_on_merge(text, pull["number"], pull["html_url"], today or dt.date.today().isoformat(), merged)
    if marked != text:
        (root / rel).write_text(marked, encoding="utf-8")
        _git(root, "add", rel)
        _git(root, "commit", "-q", "-m", f"MODIFIED: {work} approved when pull request #{pull['number']} merges")
        push(root, session, plan)
        pull = open_or_update(session, plan, base, title, describe(root, rel, marked, plan, base))
    cache = read_cache(root)
    cache[work] = {"number": pull["number"], "url": pull["html_url"], "state": "open", "work": rel}
    write_cache(root, cache)
    return pull


def sync(root: Path, work: str, session: Session | None = None) -> list[str]:
    """Read the pull request back: merged state, and change requests from listed approvers."""
    from kanon import approve, branch as branches
    entry = read_cache(root).get(work)
    session = session or sign_in(root)
    plan = branches.plan_branch(work)
    pull = call("GET", f"/repos/{session.repo}/pulls/{entry['number']}", session.token) if entry else \
        _pull_for(session, plan, "main")
    if not pull:
        return [f"no pull request for {plan}"]
    cache = read_cache(root)
    lines = []
    if pull.get("merged_at"):
        cache.pop(work, None)
        lines.append(f"pull request #{pull['number']} was merged: the work is approved")
    elif pull.get("state") == "closed":
        import datetime as dt
        cache.pop(work, None)
        rel, text = branches.work_file(root, work)
        marked = _mark_closed(text, pull["number"], pull.get("html_url", ""), dt.date.today().isoformat())
        if marked != text:
            (root / rel).write_text(marked, encoding="utf-8")
        lines.append(f"pull request #{pull['number']} was closed without merging: {rel} reopened; commit the change")
    else:
        rel, text = branches.work_file(root, work)
        approvers = branches._approvers(root)
        for review in approvals(reviews(session, pull["number"]), approvers, pull["head"]["sha"]):
            user = review["user"]["login"]
            if review["state"] == "CHANGES_REQUESTED" and review["html_url"] not in text:
                approve.record(root, rel, user, approvers, changes=review.get("body") or "see the review",
                               github_review=review["html_url"])
                text = (root / rel).read_text(encoding="utf-8")
                lines.append(f"{user} requested changes: recorded in {rel}")
            elif review["state"] == "APPROVED":
                lines.append(f"{user} approved; merge the pull request on GitHub to complete the decision")
        cache[work] = {"number": pull["number"], "url": pull["html_url"], "state": "open",
                       "work": branches.work_file(root, work)[0]}
    write_cache(root, cache)
    return lines


def protect(root: Path, approvers: list[str], branch: str = "main", run=subprocess.run) -> list[str]:
    """Branch protection with the person's own `gh` login (the App has no Administration permission)."""
    repo = repository(root)
    rules = {"required_status_checks": None, "enforce_admins": True, "restrictions": None,
             "required_pull_request_reviews": {"required_approving_review_count": 1, "require_code_owner_reviews": True,
                                               "dismiss_stale_reviews": True, "require_last_push_approval": False},
             "allow_force_pushes": False, "allow_deletions": False, "required_linear_history": False}
    steps = [["gh", "api", "-X", "PUT", f"repos/{repo}/branches/{branch}/protection", "--input", "-"],
             ["gh", "api", "-X", "PATCH", f"repos/{repo}", "-F", "allow_squash_merge=false",
              "-F", "allow_rebase_merge=false", "-F", "allow_merge_commit=true"]]
    out = []
    owners = root / ".github" / "CODEOWNERS"
    if not owners.exists():
        owners.parent.mkdir(parents=True, exist_ok=True)
        owners.write_text("# Written by kanon github protect: approvers review every change.\n* "
                          + " ".join(f"@{a}" for a in approvers) + "\n", encoding="utf-8")
        out.append(".github/CODEOWNERS written; commit it through a pull request")
    for index, step in enumerate(steps):
        result = run(step, cwd=root, input=json.dumps(rules) if index == 0 else None, capture_output=True, text=True)
        if result.returncode != 0:
            raise GitHubError(f"{' '.join(step[:4])} failed: {result.stderr.strip()}")
    out.append(f"{branch} now needs a code owner's approving review; merge commits only")
    return out


def manifest(owner_name: str, redirect: str) -> dict:
    name = f"Kanon ({owner_name})"
    name = name if len(name) <= 34 else f"Kanon ({owner_name[:25]})"  # GitHub's App name limit (K-413)
    return {"name": name, "url": "https://github.com/Bwalker01/Kanon", "redirect_url": redirect,
            "public": False, "default_permissions": dict(PERMISSIONS), "default_events": [],
            "hook_attributes": {"url": "https://example.invalid/kanon", "active": False}}


def setup(root: Path, org: str | None = None, open_browser=None, port: int = 0, wait: float = 600) -> dict:
    """GitHub's App Manifest flow, on the person's computer: create, save the key, fill kanon.toml."""
    import html
    import http.server
    import threading
    import webbrowser
    import secrets
    open_browser = open_browser or webbrowser.open
    result: dict = {}
    state = secrets.token_urlsafe(24)  # only GitHub's answer to this form is accepted (K-409)

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            from urllib.parse import parse_qs, urlparse
            query = parse_qs(urlparse(self.path).query)
            if self.path.startswith("/callback") and "code" in query and query.get("state", [""])[0] == state:
                result["code"] = query["code"][0]
                page = "<p>Kanon received GitHub's answer. You can close this tab.</p>"
            else:
                target = f"https://github.com/organizations/{org}/settings/apps/new" if org else \
                    "https://github.com/settings/apps/new"
                data = html.escape(json.dumps(manifest(org or repository(root).split("/")[0],
                                                       f"http://127.0.0.1:{server.server_port}/callback")))
                page = (f'<form id="f" method="post" action="{target}?state={state}"><input type="hidden" name="manifest" '
                        f'value="{data}"><button>Create the Kanon App on GitHub</button></form>'
                        '<script>document.getElementById("f").submit()</script>')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode())

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    open_browser(f"http://127.0.0.1:{server.server_port}/")
    deadline = time.time() + wait
    while "code" not in result and time.time() < deadline:
        time.sleep(0.2)
    server.shutdown()
    server.server_close()
    if "code" not in result:
        raise GitHubError("no answer from GitHub within 10 minutes; run kanon github setup again")
    app = call("POST", f"/app-manifests/{result['code']}/conversions", None, {})
    path = key_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        handle.write(app["pem"])
    settings_path = root / "kanon" / "kanon.toml"
    text = settings_path.read_text(encoding="utf-8")
    block = f'[github]\napp_id = {int(app["id"])}\napp_slug = "{app["slug"]}"\n'
    text = re.sub(r"\[github\]\n(?:[^\[\n].*\n?)*", block, text) if "[github]" in text else text.rstrip("\n") + "\n\n" + block
    settings_path.write_text(text, encoding="utf-8")
    open_browser(f"https://github.com/apps/{app['slug']}/installations/new")
    return {"id": app["id"], "slug": app["slug"], "key": str(path)}
