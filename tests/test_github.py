"""P1-10: GitHub mode, tested against recorded GitHub responses (no network)."""

import base64
import json
import os
import subprocess
import threading
import urllib.request

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from kanon import approve, desk, github
from kanon import branch as branches
from kanon.cli import main
from kanon.settings import validate_settings
from test_branch import REVIEW, TEXT, WORK, commit_file, git, record_review
from test_branch import repo as branch_repo  # noqa: F401  (fixture)

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PEM = KEY.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                        serialization.NoEncryption()).decode()


@pytest.fixture
def repo(branch_repo, monkeypatch):  # noqa: F811
    git(branch_repo, "remote", "add", "origin", "https://github.com/ada-dev/project")
    monkeypatch.setenv("KANON_APP_KEY", PEM)
    monkeypatch.setenv("KANON_APP_ID", "123")
    return branch_repo


class FakeGitHub:
    """Recorded responses keyed by (method, path prefix); records every call."""

    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def __call__(self, method, path, token=None, body=None, kind="token"):
        self.calls.append((method, path, body, kind))
        for (m, prefix), answer in self.responses.items():
            if m == method and path.startswith(prefix):
                return answer(body) if callable(answer) else answer
        raise github.GitHubError(f"unexpected {method} {path}")


SIGN_IN = {
    ("GET", "/app"): {"id": 123, "slug": "kanon-ada", "name": "Kanon (ada)"},
    ("GET", "/repos/ada-dev/project/installation"): {"id": 9, "repository_selection": "selected",
                                                     "permissions": {"contents": "write", "pull_requests": "write",
                                                                     "metadata": "read"}},
    ("POST", "/app/installations/9/access_tokens"): {"token": "ghs_secret", "permissions": {
        "contents": "write", "pull_requests": "write", "metadata": "read"}},
}


def test_the_key_is_read_as_pem_base64_or_file(monkeypatch, tmp_path):
    assert github.load_key().decode().startswith("-----BEGIN")
    monkeypatch.setenv("KANON_APP_KEY", base64.b64encode(PEM.encode()).decode())
    assert github.load_key() == PEM.encode()
    monkeypatch.setenv("KANON_APP_KEY", "not a key")
    with pytest.raises(github.GitHubError):
        github.load_key()
    monkeypatch.delenv("KANON_APP_KEY")
    monkeypatch.setenv("KANON_APP_KEY_FILE", str(tmp_path / "k.pem"))
    (tmp_path / "k.pem").write_text(PEM)
    assert github.load_key() == PEM.encode()


@pytest.fixture(autouse=True)
def _key_env(monkeypatch):
    monkeypatch.setenv("KANON_APP_KEY", PEM)


def test_the_jwt_is_signed_by_the_key_and_short_lived():
    token = github.make_jwt("123", PEM.encode(), now=1_000_000)
    header, claims, signature = token.split(".")
    pad = lambda s: s + "=" * (-len(s) % 4)  # noqa: E731
    data = json.loads(base64.urlsafe_b64decode(pad(claims)))
    assert data == {"iat": 999_940, "exp": 1_000_540, "iss": "123"}
    KEY.public_key().verify(base64.urlsafe_b64decode(pad(signature)), f"{header}.{claims}".encode(),
                            padding.PKCS1v15(), hashes.SHA256())


def test_check_reports_the_app_installation_and_permissions(repo, monkeypatch):
    fake = FakeGitHub(SIGN_IN)
    monkeypatch.setattr(github, "call", fake)
    lines = github.check(repo)
    assert lines[0].startswith("App: Kanon (ada) (kanon-ada), ID 123")
    assert "contents: write" in lines[2] and not any("Missing" in l for l in lines)
    assert any('app_slug = "kanon-ada"' in l for l in lines)  # kanon.toml has no [github] yet
    token_request = next(c for c in fake.calls if c[1].endswith("/access_tokens"))
    assert token_request[2] == {"repositories": ["project"], "permissions": github.PERMISSIONS}
    assert not any("ghs_secret" in l for l in lines)


def test_check_warns_about_administration(repo, monkeypatch):
    answers = dict(SIGN_IN)
    answers[("GET", "/repos/ada-dev/project/installation")] = {
        "id": 9, "permissions": {"contents": "write", "pull_requests": "write", "metadata": "read", "administration": "write"}}
    monkeypatch.setattr(github, "call", FakeGitHub(answers))
    assert any("Administration" in l for l in github.check(repo))


def test_push_refuses_other_branches_and_never_shows_the_token(repo, monkeypatch):
    session = github.Session("ada-dev/project", "ghs_secret", {}, {})
    with pytest.raises(github.GitHubError, match="only kanon"):
        github.push(repo, session, "main")
    seen = []

    def failing(cmd, **kwargs):  # stands in for git: no network in tests
        seen.append(cmd)
        header = next(c for c in cmd if "extraHeader" in c).split("Basic ", 1)[1]
        return subprocess.CompletedProcess(cmd, 1, "", f"fatal: denied for ghs_secret {header}")
    monkeypatch.setattr(github.subprocess, "run", failing)
    with pytest.raises(github.GitHubError) as error:
        github.push(repo, session, "kanon/build/plan")
    assert "ghs_secret" not in str(error.value) and "***" in str(error.value)
    assert "--force" not in seen[0] and seen[0][-1] == "refs/heads/kanon/build/plan:refs/heads/kanon/build/plan"


def item_merged(repo):
    branches.start(repo, "build", "P1-01")
    commit_file(repo, "one.txt")
    record_review(repo, "| 1 | P1-01 | Kritos | pass | None | Accepted |")
    branches.merge(repo, "build", "P1-01")


def test_the_description_lists_items_rounds_and_cost_without_a_model(repo):
    item_merged(repo)
    rel, text = branches.work_file(repo, "build")
    body = github.describe(repo, rel, text, "kanon/build/plan")
    assert github.MARKER in body and "| P1-01 | " in body and "| P1-02 | not merged |" in body
    assert "review round 1 passed" in body and "### Cost" in body and "without a model call" in body


def pr_fake(number=7):
    answers = {("GET", "/repos/ada-dev/project/pulls?state=open"): [],
               ("POST", "/repos/ada-dev/project/pulls"): {"number": number, "html_url": f"https://github.com/ada-dev/project/pull/{number}"},
               ("PATCH", f"/repos/ada-dev/project/pulls/{number}"): {"number": number, "html_url": f"https://github.com/ada-dev/project/pull/{number}"}}
    return FakeGitHub(answers)


def test_opening_the_pull_request_records_that_its_merge_approves(repo, monkeypatch):
    item_merged(repo)
    pushes = []
    monkeypatch.setattr(github, "push", lambda root, session, ref: pushes.append(ref))
    fake = pr_fake()
    monkeypatch.setattr(github, "call", fake)
    session = github.Session("ada-dev/project", "t", {}, {})
    pull = github.open_pull_request(repo, "build", session=session, today="2026-11-20")
    text = (repo / WORK).read_text()
    assert pull["number"] == 7 and pushes == ["kanon/build/plan", "kanon/build/plan"]
    assert "| P1-01 | Approved on merge of pull request #7 |" in text and "status: in-progress" in text
    assert "P1-02 | Approved on merge" not in text
    assert github.read_cache(repo)["build"]["number"] == 7
    assert not any("/actions" in c[1] or c[2] and c[2].get("event") == "APPROVE" for c in fake.calls)
    before = git(repo, "rev-parse", "HEAD")
    github.open_pull_request(repo, "build", session=session, today="2026-11-21")
    assert git(repo, "rev-parse", "HEAD") == before  # recorded once


def test_a_single_item_work_file_is_complete_when_its_pull_request_merges(repo):
    single = TEXT.replace("### 1.1 Work Items", "### 1.1 Scope").replace("| P1-01 | One | a |\n| P1-02 | Two | b |", "")
    marked = github._mark_on_merge(single, 3, "https://github.com/o/r/pull/3", "2026-11-20", [])
    assert "status: complete" in marked and "| Result | Approved on merge of pull request #3 |" in marked
    assert approve.check(marked, ["ada-dev"], "complete") == []


def review(user, state, sha, url="https://github.com/ada-dev/project/pull/7#r1", body="split it"):
    return {"user": {"login": user}, "state": state, "commit_id": sha, "html_url": url, "body": body}


def test_sync_records_change_requests_from_approvers_on_the_head_commit(repo, monkeypatch):
    item_merged(repo)
    github.write_cache(repo, {"build": {"number": 7, "url": "https://github.com/ada-dev/project/pull/7", "state": "open"}})
    head = git(repo, "rev-parse", "HEAD")
    fake = FakeGitHub({("GET", "/repos/ada-dev/project/pulls/7/reviews"): [
        review("mallory", "CHANGES_REQUESTED", head, "https://x/m"), review("ada-dev", "CHANGES_REQUESTED", "0" * 40, "https://x/old"),
        review("ada-dev", "CHANGES_REQUESTED", head)],
        ("GET", "/repos/ada-dev/project/pulls/7"): {"number": 7, "state": "open", "html_url": "u", "head": {"sha": head}}})
    monkeypatch.setattr(github, "call", fake)
    lines = github.sync(repo, "build", github.Session("ada-dev/project", "t", {}, {}))
    text = (repo / WORK).read_text()
    assert "Changes requested on GitHub by ada-dev (https://github.com/ada-dev/project/pull/7#r1)" in text
    assert "mallory" not in text and "https://x/old" not in text and lines


def test_sync_clears_a_merged_pull_request(repo, monkeypatch):
    github.write_cache(repo, {"build": {"number": 7, "url": "https://github.com/ada-dev/project/pull/7", "state": "open"}})
    monkeypatch.setattr(github, "call", FakeGitHub({("GET", "/repos/ada-dev/project/pulls/7"): {
        "number": 7, "merged_at": "2026-11-21T10:00:00Z", "state": "closed"}}))
    assert "merged" in github.sync(repo, "build", github.Session("ada-dev/project", "t", {}, {}))[0]
    assert github.read_cache(repo) == {}


def test_the_desk_lists_open_pull_requests_as_decisions(repo):
    github.write_cache(repo, {"build": {"number": 7, "url": "https://github.com/ada-dev/project/pull/7",
                                        "state": "open", "work": WORK}})
    built = desk.build(repo)
    assert any(d.url.endswith("/pull/7") for d in built.decisions)
    assert "Open on GitHub" in desk.render_html(built)


def test_protect_sets_code_owner_reviews_and_merge_commits_only(repo):
    seen = []

    def run(cmd, **kwargs):
        seen.append((cmd, kwargs.get("input")))
        return subprocess.CompletedProcess(cmd, 0, "", "")
    github.protect(repo, ["ada-dev"], run=run)
    rules = json.loads(seen[0][1])
    assert rules["required_pull_request_reviews"]["require_code_owner_reviews"] and rules["enforce_admins"]
    assert "allow_squash_merge=false" in seen[1][0] and "allow_rebase_merge=false" in seen[1][0]
    assert (repo / ".github/CODEOWNERS").read_text().strip().endswith("* @ada-dev")


def test_setup_runs_the_manifest_flow_and_saves_the_key_privately(repo, monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setattr(github, "call", FakeGitHub({("POST", "/app-manifests/abc/conversions"): {
        "id": 456, "slug": "kanon-ada", "pem": PEM}}))
    opened = []

    def browser(url):
        opened.append(url)
        if url.startswith("http://127.0.0.1"):
            page = urllib.request.urlopen(url).read().decode()  # noqa: S310  (local test server)
            assert "settings/apps/new" in page and "pull_requests" in page
            threading.Thread(target=lambda: urllib.request.urlopen(url + "callback?code=abc").read()).start()  # noqa: S310
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    app = github.setup(repo, open_browser=browser)
    key = github.key_path()
    assert app["id"] == 456 and key.read_text() == PEM and key.stat().st_mode & 0o077 == 0
    assert 'app_id = 456' in (repo / "kanon/kanon.toml").read_text()
    assert opened[-1] == "https://github.com/apps/kanon-ada/installations/new"
    assert validate_settings((repo / "kanon/kanon.toml").read_text()) == []


def test_setup_and_protect_are_refused_inside_an_assistant(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    monkeypatch.setenv("CLAUDECODE", "1")
    assert main(["github", "setup"]) == 2 and main(["github", "protect"]) == 2
    assert "refused inside an assistant session" in capsys.readouterr().out


def test_settings_refuse_a_committed_key():
    text = '[kanon]\nreview_round_limit = 3\napprovers = ["ada-dev"]\n\n[github]\napp_id = "x"\nprivate_key = "y"\n'
    messages = [p.message for p in validate_settings(text)]
    assert any("numeric ID" in m for m in messages) and any("never be committed" in m for m in messages)


def test_sync_denies_the_connectors_writing_tools(repo):
    from kanon import sync as ksync
    deny = ksync.deny_rules(repo)
    for tool in ("merge_pull_request", "pull_request_review_write", "create_pull_request", "push_files"):
        assert f"mcp__github__{tool}" in deny
    assert "mcp__github__pull_request_read" not in deny
