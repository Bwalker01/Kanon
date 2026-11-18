"""The Desk: a generated, per-person view of what waits on someone (Atlas's output).

Everything here is derived from committed work files, the shared settings, Git history and the
person's profile. Nothing is committed: output goes to kanon/local/, which Git ignores.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from kanon import profile as profiles
from kanon.verify import _body, _sections, _table

LOCAL = "kanon/local"
OUTPUTS = (f"{LOCAL}/DESK.md", f"{LOCAL}/desk.html", f"{LOCAL}/STATUS.md")
CLOSED = ("complete", "parked")


@dataclass
class Decision:
    id: str
    work: str
    title: str
    summary: str
    needed: str


@dataclass
class Action:
    id: str
    work: str
    work_title: str
    title: str
    assignee: str
    blocks: list[str]
    done: bool
    steps: list[str] = field(default_factory=list)


@dataclass
class LateReview:
    work: str
    work_title: str
    round: str
    outcome: str


@dataclass
class Work:
    path: str
    title: str
    status: str
    summary: str


@dataclass
class Desk:
    person: str
    branch: str
    generated: str
    decisions: list[Decision]
    actions: list[Action]
    reviews: list[LateReview]
    work: list[Work]
    recent: list[str]
    notes: list[str]


def _title(lines: list[str]) -> str:
    return next((l[2:].strip() for l in lines if l.startswith("# ")), "Untitled")


def _quote_field(lines: list[str], label: str) -> str:
    """Text of a '> **Label:** ...' line in the summary block, joined with its continuation lines."""
    out, capturing = [], False
    for line in lines:
        if not line.startswith(">"):
            if capturing:
                break
            continue
        text = line[1:].strip()
        if text.startswith(f"**{label}:**"):
            capturing = True
            out.append(text[len(label) + 5:].strip())
        elif capturing and text.startswith("**"):
            break
        elif capturing:
            out.append(text)
    return " ".join(out).strip()


def _split(cell: str) -> list[str]:
    return [c.strip(" `") for c in re.split(r"[,;]", cell) if c.strip(" `-")]


def parse_work(rel: str, text: str) -> tuple[Work, Decision | None, list[Action], list[LateReview]]:
    meta, lines, _ = _body(text)
    meta = meta or {}
    title = _title(lines)
    status = str(meta.get("status", ""))
    work = Work(rel, title, status, _quote_field(lines, "Summary"))
    decision = None
    if status == "awaiting-approval":
        decision = Decision("", rel, title, work.summary, _quote_field(lines, "Decision needed"))

    sections = _sections(lines)
    actions: list[Action] = []
    span = sections.get("Actions")
    if span:
        block = lines[span[0]:span[1]]
        rows = _table(block)
        if rows and rows[0][0].lower() == "id":
            header = [h.lower() for h in rows[0]]
            col = {name: header.index(name) for name in ("id", "action", "assignee", "blocks", "done") if name in header}
            for row in rows[1:]:
                get = lambda key: row[col[key]] if key in col and col[key] < len(row) else ""  # noqa: E731
                actions.append(Action(get("id"), rel, title, get("action"), get("assignee"),
                                      _split(get("blocks")), get("done").lower() in ("yes", "done", "true")))
        current = None
        for line in block:
            heading = re.match(r"^### ([A-Za-z]+-\d+)\b", line)
            if heading:
                current = next((a for a in actions if a.id == heading.group(1)), None)
                continue
            step = re.match(r"^\s*\d+\.\s+(.*)", line)
            if current and step:
                current.steps.append(step.group(1).strip())

    reviews: list[LateReview] = []
    span = sections.get("Review")
    if span:
        for row in _table(lines[span[0]:span[1]])[1:]:
            outcome = row[-1]
            lower = outcome.lower()
            if "owner decides" in lower and "owner reviewed" not in lower:
                reviews.append(LateReview(rel, title, row[0], outcome))
    return work, decision, actions, reviews


def order_actions(actions: list[Action]) -> list[Action]:
    """Dependency order: an action comes before every action it blocks. Stable otherwise."""
    key = lambda a: (a.work, a.id)  # noqa: E731
    index = {(a.work, a.id): a for a in actions}
    waiting = {key(a): 0 for a in actions}
    for a in actions:
        for target in a.blocks:
            if (a.work, target) in index:
                waiting[(a.work, target)] += 1
    ready = [a for a in actions if waiting[key(a)] == 0]
    ordered: list[Action] = []
    while ready:
        current = ready.pop(0)
        ordered.append(current)
        for target in current.blocks:
            k = (current.work, target)
            if k in waiting:
                waiting[k] -= 1
                if waiting[k] == 0:
                    ready.append(index[k])
    ordered += [a for a in actions if a not in ordered]  # cycles: keep remaining in file order
    return ordered


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True).stdout.strip()


def build(root: Path, today: dt.datetime | None = None) -> Desk:
    notes: list[str] = []
    try:
        person = profiles.load()
    except ValueError as error:
        person, _ = None, notes.append(f"profile ignored: {error}")
    github = (person.github if person else "").lower()
    if not github:
        notes.append("no GitHub username in the profile: showing every person's items (see `kanon profile`)")
    try:
        settings = tomllib.loads((root / "kanon/kanon.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        settings = {}
    approvers = [a.lower() for a in settings.get("kanon", {}).get("approvers", []) if isinstance(a, str)]
    may_approve = not github or github in approvers

    decisions, actions, reviews, work = [], [], [], []
    for path in sorted((root / "kanon/work").glob("*.md")):
        rel = path.relative_to(root).as_posix()
        w, d, acts, revs = parse_work(rel, path.read_text(encoding="utf-8"))
        if w.status not in CLOSED:
            work.append(w)
        if d and may_approve:
            decisions.append(d)
        actions += [a for a in acts if not a.done and (not github or a.assignee.lower() == github)]
        if may_approve:
            reviews += revs
    for number, decision in enumerate(decisions, 1):
        decision.id = f"R-{number}"
    recent = [l for l in _git(root, "log", "-n", "40", "--format=%as %s").splitlines()
              if re.match(r"^\S+ (ADDED|MODIFIED|REMOVED):", l)][:12]
    when = (today or dt.datetime.now()).strftime("%Y-%m-%d %H:%M")
    name = (person.name or person.github) if person else "everyone"
    return Desk(name, _git(root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown", when,
                decisions, order_actions(actions), reviews, work, recent, notes)


# ---------------------------------------------------------------- rendering

def render_markdown(desk: Desk) -> str:
    out = [f"# Desk: {desk.person}", "",
           f"> **Summary:** {len(desk.decisions)} decisions, {len(desk.actions)} actions and "
           f"{len(desk.reviews)} late reviews on branch `{desk.branch}`. Generated {desk.generated}; "
           "never edit or commit this file.", ""]
    out += ["## Decide", ""]
    out += [f"- **{d.id}:** {d.title}. {d.needed} Read `{d.work}`. Reply `{d.id} approve` or `{d.id} changes: ...`."
            for d in desk.decisions] or ["Nothing to decide."]
    out += ["", "## Do", ""]
    for a in desk.actions:
        out.append(f"### {a.id}: {a.title}")
        out.append(f"From `{a.work}`." + (f" Blocks {', '.join(a.blocks)}." if a.blocks else ""))
        out += [f"{n}. {s}" for n, s in enumerate(a.steps, 1)] + [""]
    if not desk.actions:
        out += ["Nothing to do.", ""]
    out += ["## Review Later", ""]
    out += [f"- `{r.work}`, round {r.round}: {r.outcome}" for r in desk.reviews] or ["Nothing waiting."]
    out += ["", "## Status", "", "See `kanon/local/STATUS.md` and `kanon/docs/roadmap.md`."]
    out += [""] + [f"Note: {n}" for n in desk.notes]
    return "\n".join(out).rstrip() + "\n"


def render_status(desk: Desk) -> str:
    out = ["# Project Status", "",
           f"> **Summary:** {len(desk.work)} pieces of work open on branch `{desk.branch}`. "
           f"Generated {desk.generated}; plan in `kanon/docs/roadmap.md`.", "", "## Work in Progress", ""]
    out += [f"- **{w.title}** ({w.status}): {w.summary} `{w.path}`" for w in desk.work] or ["None."]
    out += ["", "## Recent Changes", ""] + ([f"- {r}" for r in desk.recent] or ["None."])
    return "\n".join(out) + "\n"


def render_html(desk: Desk) -> str:
    e = html.escape
    decide = "".join(
        f'<article class="card"><header><span class="tag">{e(d.id)}</span><h3>{e(d.title)}</h3></header>'
        f'<p>{e(d.needed)}</p><details><summary>Read</summary><p>{e(d.summary)}</p>'
        f'<p class="path">{e(d.work)}</p></details>'
        f'<div class="row"><button data-copy="{e(d.id)} approve">Copy: {e(d.id)} approve</button>'
        f'<button data-copy="{e(d.id)} changes: ">Copy: {e(d.id)} changes</button></div></article>'
        for d in desk.decisions) or '<p class="empty">Nothing to decide.</p>'
    do = ""
    for a in desk.actions:
        key = f"{a.work}#{a.id}"
        steps = "".join(
            f'<li><label><input type="checkbox" data-key="{e(key)}#{n}"> {e(s)}</label></li>'
            for n, s in enumerate(a.steps, 1))
        blocks = f'<span class="muted">Blocks {e(", ".join(a.blocks))}</span>' if a.blocks else ""
        do += (f'<article class="card action" data-action="{e(key)}"><header><span class="tag">{e(a.id)}</span>'
               f'<h3>{e(a.title)}</h3>{blocks}</header><div class="bar"><span></span></div>'
               f'<ol>{steps}</ol><p class="path">{e(a.work)}</p>'
               f'<div class="row"><button data-copy="{e(a.id)} done">Copy: {e(a.id)} done</button></div></article>')
    do = do or '<p class="empty">Nothing to do.</p>'
    later = "".join(f'<li><strong>{e(r.work_title)}</strong>, round {e(r.round)}: {e(r.outcome)}</li>'
                    for r in desk.reviews) or '<li class="empty">Nothing waiting.</li>'
    work = "".join(f'<li><strong>{e(w.title)}</strong> <span class="tag">{e(w.status)}</span> {e(w.summary)}</li>'
                   for w in desk.work) or '<li class="empty">None.</li>'
    recent = "".join(f"<li>{e(r)}</li>" for r in desk.recent) or '<li class="empty">None.</li>'
    notes = "".join(f'<p class="note">{e(n)}</p>' for n in desk.notes)
    data = e(json.dumps({"branch": desk.branch}))
    return f"""<!doctype html>
<!-- Generated by kanon desk. Do not edit or commit. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kanon Desk</title>
<style>
:root{{--bg:#f7f6f2;--card:#fff;--ink:#1f2328;--muted:#656d76;--line:#d8dee4;--accent:#3b5bdb;--done:#2f9e44}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16181d;--card:#1f232a;--ink:#e6edf3;--muted:#8b949e;--line:#30363d;--accent:#748ffc;--done:#51cf66}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}
main{{max-width:860px;margin:0 auto;padding:16px}}h1{{font-size:1.4rem;margin:.2rem 0}}
h2{{font-size:1rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:1.6rem 0 .6rem}}
h3{{font-size:1rem;margin:0}}.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:0 0 10px}}
header{{display:flex;gap:8px;align-items:center;flex-wrap:wrap}}.tag{{font:600 .75rem ui-monospace,monospace;border:1px solid var(--line);border-radius:6px;padding:1px 6px}}
.muted,.path,.empty,.note{{color:var(--muted)}}.path{{font:.8rem ui-monospace,monospace;overflow-wrap:anywhere}}
.bar{{height:6px;background:var(--line);border-radius:3px;margin:8px 0;overflow:hidden}}.bar span{{display:block;height:100%;width:0;background:var(--done);transition:width .2s}}
ol{{padding-left:1.2rem;margin:.4rem 0}}li{{margin:.25rem 0}}input:checked+*,label:has(input:checked){{color:var(--muted);text-decoration:line-through}}
.row{{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}}button{{background:none;color:var(--accent);border:1px solid var(--accent);border-radius:6px;padding:4px 10px;font:inherit;cursor:pointer}}
button.ok{{color:var(--done);border-color:var(--done)}}ul{{padding-left:1.1rem}}
</style></head><body><main>
<h1>Desk: {e(desk.person)}</h1>
<p class="muted">Branch {e(desk.branch)}. Generated {e(desk.generated)} by Atlas. Ticks stay in this browser; tell your assistant when an action is done.</p>
{notes}
<h2>Decide ({len(desk.decisions)})</h2>{decide}
<h2>Do ({len(desk.actions)})</h2>{do}
<h2>Review later ({len(desk.reviews)})</h2><ul>{later}</ul>
<h2>Status</h2><ul>{work}</ul><h3>Recent changes</h3><ul>{recent}</ul>
<script type="application/json" id="desk-data">{data}</script>
<script>
(function(){{
  var store={{get:function(k){{try{{return localStorage.getItem(k)}}catch(e){{return null}}}},set:function(k,v){{try{{localStorage.setItem(k,v)}}catch(e){{}}}}}};
  function update(card){{var boxes=card.querySelectorAll('input[type=checkbox]');var done=0;
    boxes.forEach(function(b){{if(b.checked)done++}});var bar=card.querySelector('.bar span');
    if(bar)bar.style.width=(boxes.length?Math.round(100*done/boxes.length):0)+'%';}}
  document.querySelectorAll('.action').forEach(function(card){{
    card.querySelectorAll('input[type=checkbox]').forEach(function(b){{
      b.checked=store.get('kanon-desk:'+b.dataset.key)==='1';
      b.addEventListener('change',function(){{store.set('kanon-desk:'+b.dataset.key,b.checked?'1':'0');update(card)}});}});
    update(card);}});
  document.querySelectorAll('button[data-copy]').forEach(function(btn){{btn.addEventListener('click',function(){{
    var text=btn.dataset.copy;var ok=function(){{btn.classList.add('ok');btn.textContent='Copied: '+text}};
    if(navigator.clipboard){{navigator.clipboard.writeText(text).then(ok,function(){{window.prompt('Copy this reply:',text)}})}}
    else{{window.prompt('Copy this reply:',text)}}}});}});
}})();
</script>
</main></body></html>
"""


def write(root: Path, today: dt.datetime | None = None) -> Desk:
    desk = build(root, today)
    folder = root / LOCAL
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "DESK.md").write_text(render_markdown(desk), encoding="utf-8")
    (folder / "STATUS.md").write_text(render_status(desk), encoding="utf-8")
    (folder / "desk.html").write_text(render_html(desk), encoding="utf-8")
    return desk
