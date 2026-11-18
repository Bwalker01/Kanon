"""The Desk: a generated, per-person view of what waits on someone (Atlas's output).

Everything here is derived from committed work files, the shared settings, Git history and the
person's profile. Nothing is committed: output goes to kanon/local/, which Git ignores.
"""

from __future__ import annotations

import datetime as dt
import html
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


def slug(rel: str) -> str:
    """Stable short name for a work file: its file name without the date or extension."""
    name = Path(rel).stem
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name)


DONE_WORDS = ("yes", "done", "true")


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

    @property
    def assignees(self) -> list[str]:
        return [a.lstrip("@").lower() for a in _split(self.assignee)]

    @property
    def reply(self) -> str:
        return f"done {slug(self.work)} {self.id}"


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
        if rows and "id" in [h.lower() for h in rows[0]]:
            header = [h.lower() for h in rows[0]]
            col = {name: header.index(name) for name in ("id", "action", "assignee", "blocks", "done") if name in header}
            for row in rows[1:]:
                get = lambda key: row[col[key]] if key in col and col[key] < len(row) else ""  # noqa: E731
                actions.append(Action(get("id"), rel, title, get("action"), get("assignee"),
                                      _split(get("blocks")), get("done").lower().startswith(DONE_WORDS)))
        current = None
        for line in block:
            if line.startswith("#"):
                heading = re.match(r"^### ([A-Za-z]+-\d+)\b", line)
                current = next((a for a in actions if heading and a.id == heading.group(1)), None)
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
        actions += [a for a in acts if not a.done and (
            not github or github in a.assignees or (not a.assignees and may_approve))]
        if may_approve:
            reviews += revs
    for decision in decisions:
        decision.id = slug(decision.work)
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
    out += [f"- **{d.title}:** {d.needed} Read `{d.work}`. Reply `approve {d.id}` or `changes {d.id}: ...`."
            for d in desk.decisions] or ["Nothing to decide."]
    out += ["", "## Do", ""]
    for a in desk.actions:
        out.append(f"### {a.id}: {a.title}")
        out.append(f"From `{a.work}`." + (f" Blocks {', '.join(a.blocks)}." if a.blocks else "")
                   + f" When done, reply `{a.reply}`.")
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


def _inline(text: str) -> str:
    """Escaped text with Markdown `**bold**` and `code` shown as such (K-244)."""
    out = html.escape(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", out)


def _lead(text: str, limit: int) -> str:
    """Plain, escaped text cut at a word boundary with an ellipsis (K-243)."""
    plain = text.replace("**", "").replace("`", "")
    if len(plain) > limit:
        cut = plain[:limit].rsplit(" ", 1)[0] if " " in plain[:limit] else plain[:limit]
        plain = cut.rstrip(" ,;:.") + "\u2026"
    return html.escape(plain)


def _reply_box(text: str, label: str) -> str:
    e = html.escape
    return (f'<div class="reply"><input class="reply-text" readonly value="{e(text)}" aria-label="{e(label)}">'
            f'<button type="button" class="btn primary" data-copy="{e(text)}">Copy</button>'
            f'<span class="hint" aria-live="polite"></span></div>')


def _card(kind: str, chips: str, title: str, lead: str, body: str, extra_class: str = "") -> str:
    e = html.escape
    return (f'<details class="card {kind} {extra_class}"><summary><span class="chips">{chips}</span>'
            f'<span class="title">{e(title)}</span><span class="lead">{lead}</span>'
            f'<span class="chevron" aria-hidden="true"></span></summary><div class="body">{body}</div></details>')


def render_html(desk: Desk) -> str:
    e = html.escape
    chip = lambda text, tone="": f'<span class="chip {tone}">{e(text)}</span>'  # noqa: E731

    decide = "".join(_card(
        "decision", chip("Decision", "accent"), d.title, e(d.needed),
        f'<p>{_inline(d.summary)}</p><p class="path">{e(d.work)}</p>'
        f'<h4>Reply</h4>{_reply_box(f"approve {d.id}", "Approve reply")}'
        f'{_reply_box(f"changes {d.id}: ", "Request changes reply")}')
        for d in desk.decisions) or '<p class="empty">Nothing to decide.</p>'

    do = ""
    for a in desk.actions:
        key = f"{a.work}#{a.id}"
        steps = "".join(f'<li><label><input type="checkbox" data-key="{e(key)}#{n}"><span>{e(s)}</span></label></li>'
                        for n, s in enumerate(a.steps, 1)) or '<li class="empty">No steps recorded.</li>'
        chips = chip(a.id) + (chip("Blocks " + ", ".join(a.blocks), "warn") if a.blocks else "")
        lead = (f'<span class="progress" data-action="{e(key)}"><span class="bar"><span></span></span>'
                f'<span class="count">0/{len(a.steps)}</span></span>')
        do += _card("action", chips, a.title, lead,
                    f'<ol class="steps">{steps}</ol><p class="path">From {e(a.work)}</p>'
                    f'<h4>When done, reply</h4>{_reply_box(a.reply, "Done reply")}', "tracked")
    do = do or '<p class="empty">Nothing to do.</p>'

    later = "".join(_card("review", chip(f"Round {r.round}"), r.work_title, _lead(r.outcome, 90),
                          f'<p>{_inline(r.outcome)}</p><p class="path">{e(r.work)}</p>')
                    for r in desk.reviews) or '<p class="empty">Nothing waiting.</p>'

    work = "".join(_card("work", chip(w.status, "muted"), w.title, _lead(w.summary, 110),
                         f'<p>{_inline(w.summary)}</p><p class="path">{e(w.path)}</p>')
                   for w in desk.work) or '<p class="empty">No open work.</p>'
    recent = "".join(f"<li>{e(r)}</li>" for r in desk.recent) or '<li class="empty">None.</li>'
    notes = "".join(f'<p class="note">{_inline(n)}</p>' for n in desk.notes)

    tabs = [("decide", "Decide", len(desk.decisions), decide), ("do", "Do", len(desk.actions), do),
            ("later", "Review later", len(desk.reviews), later),
            ("status", "Status", len(desk.work), work + f'<h3>Recent changes</h3><ul class="recent">{recent}</ul>')]
    first = next((t[0] for t in tabs if t[2]), "status")
    urgent = "true" if first in ("decide", "do") else "false"  # waiting items outrank a remembered tab (K-246)
    tab_buttons = "".join(
        f'<button type="button" role="tab" class="tab" id="tab-{k}" aria-controls="panel-{k}" data-tab="{k}">'
        f'{e(label)}<span class="badge{" zero" if n == 0 else ""}">{n}</span></button>'
        for k, label, n, _ in tabs)
    panels = "".join(f'<section role="tabpanel" class="panel" id="panel-{k}" aria-labelledby="tab-{k}">'
                     f'<h2 class="panel-title">{e(label)}</h2>{content}</section>'
                     for k, label, _, content in tabs)

    return f"""<!doctype html>
<!-- Generated by kanon desk. Do not edit or commit. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kanon Desk</title>
<style>
:root{{--bg:#f4f3ef;--card:#fff;--ink:#1d2127;--muted:#5f6772;--line:#dde1e6;--accent:#3451c7;--accent-soft:#e8ecfb;
--done:#2b8a3e;--warn:#b35c00;--warn-soft:#fff1e0;--shadow:0 1px 2px rgba(0,0,0,.06)}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14161a;--card:#1d2026;--ink:#e7ebf0;--muted:#98a1ad;--line:#2e333b;
--accent:#8299ff;--accent-soft:#232a45;--done:#57c26a;--warn:#f0a050;--warn-soft:#3a2a17;--shadow:none}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,sans-serif}}
main{{max-width:880px;margin:0 auto;padding:16px}}
.top h1{{font-size:1.35rem;margin:0}}.top p{{margin:.2rem 0 0;color:var(--muted);font-size:.9rem}}
.tabs{{display:flex;gap:4px;margin:16px 0 12px;border-bottom:1px solid var(--line);overflow-x:auto}}
.tab{{appearance:none;border:0;background:none;color:var(--muted);font:600 .95rem system-ui,sans-serif;padding:10px 14px;
cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-1px;white-space:nowrap;display:flex;gap:8px;align-items:center}}
.tab[aria-selected=true]{{color:var(--ink);border-bottom-color:var(--accent)}}.tab:focus-visible{{outline:2px solid var(--accent)}}
.badge{{background:var(--accent);color:#fff;border-radius:999px;font-size:.75rem;padding:0 8px;min-width:22px;text-align:center}}
.badge.zero{{background:var(--line);color:var(--muted)}}
.js .tabs{{display:flex}} .tabs{{display:none}} .js .panel{{display:none}} .js .panel.active{{display:block}}
.js .panel-title{{display:none}} .panel-title{{font-size:1rem;margin:20px 0 8px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:0 0 10px;box-shadow:var(--shadow)}}
.card summary{{list-style:none;cursor:pointer;padding:12px 14px;display:grid;grid-template-columns:auto 1fr auto;
grid-template-areas:"chips chips chev" "title title chev" "lead lead chev";gap:4px 10px;align-items:center}}
.card summary::-webkit-details-marker{{display:none}}
.chips{{grid-area:chips;display:flex;gap:6px;flex-wrap:wrap}}.title{{grid-area:title;font-weight:650}}
.lead{{grid-area:lead;color:var(--muted);font-size:.9rem}}
.chevron{{grid-area:chev;width:10px;height:10px;border-right:2px solid var(--muted);border-bottom:2px solid var(--muted);
transform:rotate(45deg);transition:transform .15s}}.card[open] .chevron{{transform:rotate(225deg)}}
.body{{padding:0 14px 14px;border-top:1px solid var(--line)}}.body h4{{margin:14px 0 6px;font-size:.85rem;color:var(--muted)}}
.chip{{font:600 .72rem ui-monospace,monospace;border-radius:6px;padding:2px 7px;background:var(--bg);border:1px solid var(--line)}}
.chip.accent{{background:var(--accent-soft);border-color:transparent;color:var(--accent)}}
.chip.warn{{background:var(--warn-soft);border-color:transparent;color:var(--warn)}}.chip.muted{{color:var(--muted)}}
.path{{font:.8rem ui-monospace,monospace;color:var(--muted);overflow-wrap:anywhere}}
.progress{{display:inline-flex;align-items:center;gap:8px}}.bar{{width:120px;height:6px;background:var(--line);border-radius:3px;overflow:hidden}}
.bar span{{display:block;height:100%;width:0;background:var(--done);transition:width .2s}}.count{{font-size:.8rem}}
.steps{{padding-left:1.3rem;margin:12px 0}}.steps li{{margin:.4rem 0}}
.steps label{{display:flex;gap:8px;align-items:flex-start;cursor:pointer}}.steps input{{margin-top:.3rem}}
.steps input:checked+span{{color:var(--muted);text-decoration:line-through}}
.reply{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:6px 0}}
.reply-text{{flex:1 1 220px;font:.9rem ui-monospace,monospace;padding:7px 9px;border:1px solid var(--line);border-radius:8px;
background:var(--bg);color:var(--ink)}}
.btn{{font:600 .9rem system-ui,sans-serif;border-radius:8px;padding:7px 14px;cursor:pointer;border:1px solid var(--accent);
background:var(--card);color:var(--accent)}}.btn.primary{{background:var(--accent);color:#fff}}.btn:focus-visible{{outline:2px solid var(--ink)}}
.btn.ok{{background:var(--done);border-color:var(--done)}}.hint{{font-size:.82rem;color:var(--muted)}}
.empty,.note{{color:var(--muted)}}.recent{{padding-left:1.1rem;font-size:.9rem}}
</style></head><body><main>
<header class="top"><h1>Desk: {e(desk.person)}</h1>
<p>Branch {e(desk.branch)} · generated {e(desk.generated)} by Atlas · ticks stay in this browser; tell your assistant when an action is done.</p></header>
{notes}
<nav class="tabs" role="tablist">{tab_buttons}</nav>
{panels}
<script>
(function(){{
  document.documentElement.classList.add('js');
  var store={{get:function(k){{try{{return localStorage.getItem(k)}}catch(e){{return null}}}},
              set:function(k,v){{try{{localStorage.setItem(k,v)}}catch(e){{}}}}}};
  var tabs=document.querySelectorAll('.tab');
  function show(name){{
    tabs.forEach(function(t){{var on=t.dataset.tab===name;t.setAttribute('aria-selected',on);t.tabIndex=on?0:-1;
      document.getElementById('panel-'+t.dataset.tab).classList.toggle('active',on);}});
    store.set('kanon-desk:tab',name);
  }}
  tabs.forEach(function(t){{t.addEventListener('click',function(){{show(t.dataset.tab)}});
    t.addEventListener('keydown',function(ev){{var list=Array.prototype.slice.call(tabs);var i=list.indexOf(t);
      if(ev.key==='ArrowRight'||ev.key==='ArrowLeft'){{var n=list[(i+(ev.key==='ArrowRight'?1:list.length-1))%list.length];n.focus();show(n.dataset.tab)}}}});}});
  var saved=store.get('kanon-desk:tab');show(!{urgent}&&saved&&document.getElementById('panel-'+saved)?saved:'{first}');
  function progress(card){{var boxes=card.querySelectorAll('input[type=checkbox]');var done=0;
    boxes.forEach(function(b){{if(b.checked)done++}});
    var bar=card.querySelector('.bar span');if(bar)bar.style.width=(boxes.length?Math.round(100*done/boxes.length):0)+'%';
    var count=card.querySelector('.count');if(count)count.textContent=done+'/'+boxes.length;}}
  document.querySelectorAll('.card.tracked').forEach(function(card){{
    card.querySelectorAll('input[type=checkbox]').forEach(function(b){{
      b.checked=store.get('kanon-desk:'+b.dataset.key)==='1';
      b.addEventListener('change',function(){{store.set('kanon-desk:'+b.dataset.key,b.checked?'1':'0');progress(card)}});}});
    progress(card);}});
  function copy(btn){{
    var box=btn.parentNode.querySelector('.reply-text');var hint=btn.parentNode.querySelector('.hint');var text=btn.dataset.copy;
    box.focus();box.select();try{{box.setSelectionRange(0,text.length)}}catch(e){{}}
    function result(ok){{if(ok){{btn.textContent='Copied';btn.classList.add('ok');hint.textContent='';}}
      else{{hint.textContent='Selected: press Ctrl+C (Cmd+C on a Mac)';}}
      setTimeout(function(){{btn.textContent='Copy';btn.classList.remove('ok')}},2000);}}
    var ok=false;try{{ok=document.execCommand('copy')}}catch(e){{ok=false}}
    if(ok){{result(true);return}}
    if(navigator.clipboard&&navigator.clipboard.writeText){{
      navigator.clipboard.writeText(text).then(function(){{result(true)}},function(){{box.select();result(false)}});
    }}else{{result(false)}}
  }}
  document.querySelectorAll('button[data-copy]').forEach(function(b){{
    b.addEventListener('click',function(ev){{ev.preventDefault();ev.stopPropagation();copy(b)}});}});
  document.querySelectorAll('.reply-text').forEach(function(box){{box.addEventListener('focus',function(){{box.select()}})}});
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
