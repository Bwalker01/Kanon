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
    key = serialization.load_pem_private_key(key_pem, password=None)
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
    token: str
    installation: dict
    app: dict
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
        lines.append(f"Add to kanon/kanon.toml: [github] app_id = {session.app.get('id')}, "
                     f"app_slug = \"{session.app.get('slug')}\"")
    return lines


# ---------------------------------------------------------------- push and pull requests

def push(root: Path, session: Session, branch: str) -> None:
    """Push a branch with the App's token; never forces."""
    if not re.fullmatch(r"kanon/[A-Za-z0-9._/-]+", branch):
        raise GitHubError(f"Kanon pushes only kanon/* branches, not {branch}")
    header = base64.b64encode(f"x-access-token:{session.token}".encode()).decode()
    url = f"https://github.com/{session.repo}.git"
    result = subprocess.run(["git", "-c", "credential.helper=", "-c", f"http.https://github.com/.extraHeader=Authorization: Basic {header}",
                             "push", url, f"refs/heads/{branch}:refs/heads/{branch}"],
                            cwd=root, capture_output=True, text=True)
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
            "Approve with a review on GitHub; Kanon records it with `kanon github sync`."]
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
