---
type: work
status: awaiting-approval
updated: 2026-11-25
---

# Desk Dark Theme

> **Summary:** The Desk (`kanon/local/desk.html`) uses its dark palette by default, since the Claude app's browser
> pane renders local files in light mode and so never showed the existing dark media query.
> **Decision needed:** View the dark Desk (A-1), then merge the App's pull request; the merge approves the plan and the result.

## 1. Plan

| Field | Value |
|---|---|
| Output | The stylesheet in `desk.render_html` (`src/kanon/desk.py`), a test in `tests/test_desk.py` |
| Inputs | The owner's request in chat on 2026-11-25 (section 2); the existing `prefers-color-scheme:dark` palette in `render_html`; the browser pane's behaviour, from its tool description: "local documents and static HTML previews always render light" |
| Acceptance | See 1.2 |
| Creator | Claude (assistant) |
| Reviewer | Kritos (independent) |

### 1.1 Design

| Part | Choice |
|---|---|
| Palette | The existing dark values become the `:root` defaults; the light palette and the media query are removed, so the Desk looks the same in every browser. `color-scheme: dark` is set so form controls and scroll bars match. |
| Contrast | Text on the accent colour (`.badge`, `.btn.primary`) changes from white to the background colour: white on `#8299ff` is about 2.6:1, below WCAG AA's 4.5:1 for normal text (assessment, WCAG relative luminance formula); `#14161a` on `#8299ff` is about 6.9:1. |
| Branches | One item, DT-1, on `kanon/desk-dark-theme/DT-1`, merged into `kanon/desk-dark-theme/plan` (cut from `main` at 513dccc) after review. |
| Sequence | 1. This plan is committed on its own. 2. DT-1 built and reviewed by Kritos. 3. Merged into the plan branch; Cost recorded. 4. The assistant runs `kanon github pr desk-dark-theme`, `kanon github notes` and `kanon github ready`. 5. The owner merges; the merge approves the plan and the result. |

### 1.2 Acceptance

| Check | Confirmed by |
|---|---|
| The generated HTML sets the dark values on `:root`, sets `color-scheme: dark`, and has no `prefers-color-scheme` query or light background value (`#f4f3ef`) | Test |
| Text on the accent colour uses the background colour | Test |
| The Desk opened in the browser pane is dark | The owner views it in the pane (A-1); the browser pane cannot screenshot local files. Confirmation recorded in section 4 |
| `uv run pytest -q` and `uv run kanon verify` pass | Command output |

### 1.3 Work Items

| ID | Item | Delivers |
|---|---|---|
| DT-1 | Dark palette | Stylesheet change, test |

## 2. Questions

| Date | Question | Answer |
|---|---|---|
| 2026-11-25 | Desk theme (owner in chat) | "when you get a second, give the desk a dark theme palette" |

## 3. Actions

| ID | Action | Assignee | Blocks | Done |
|---|---|---|---|---|
| A-1 | Confirm the Desk looks right in the dark palette | Bwalker01 | | no |

### A-1: View the Dark Desk

1. In the Claude app's browser pane, open the Desk the assistant built from this branch (it opens it for you).
2. Check the tabs, the count badges, the cards and the Copy button read clearly.
3. Confirm: reply `done desk-dark-theme A-1`, or describe what looks wrong, before merging the pull request.

## 4. Review

| Round | Items | Reviewer | Verdict | Blocking | Outcome |
|---|---|---|---|---|---|
| R1 | DT-1 (88e8b01) | Kritos (`kritos-reviewer` agent) | pass | None | Design and acceptance met. Contrast confirmed: white on `#8299ff` 2.64:1, `#14161a` on `#8299ff` 6.86:1; every text pair on the dark palette meets AA (4.5:1), and the Copy button after copying improves from 1.88:1 to 8.05:1. The one suite failure (WinError 206, path too long) is the checkout's location; the test passes in the main checkout. F1: screenshot row revised to the owner's view (A-1). F2: Cost filled. F3: `--line` borders are about 1.3:1 against the cards, below WCAG 1.4.11's 3:1, unchanged from the old dark palette; recorded as a known limit. F4: the test matches exact stylesheet strings. |

## 5. Decision

| Item | Decision | Date | Basis |
|---|---|---|---|
| DT-1 | Approved on merge of pull request #11 | 2026-11-25 | https://github.com/Bwalker01/Kanon/pull/11; a code owner's review is required to merge |

## 6. Cost

Window: `kanon usage --since 00d4eee` (the plan commit). Main-session output in the window includes the cloud session parity plan rounds P2 and P3 (assessment).

| Step | Output (main) | Output (subagents) | Cache writes | Cache reads | Estimated cost |
|---|---|---|---|---|---|
| DT-1 build and review R1 (window shared with cloud session parity rounds P2 and P3) | 15,180 | 29,654 | 110,679 | 4,590,770 | not yet calculated (Claude Code has not updated its estimate) |
