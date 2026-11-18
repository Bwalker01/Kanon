import pytest

from kanon.schema import DOC_TYPES, REQUIRED_FRONTMATTER, validate
from kanon.templates import TEMPLATE_NAMES, render

VALUES = dict(
    date="2026-11-16",
    title="Example",
    summary="An example document.",
    number="001",
)
MARKDOWN = [n for n in TEMPLATE_NAMES if n.endswith(".md") and not n.startswith(("claude/", "rules-"))]


@pytest.mark.parametrize("name", MARKDOWN)
def test_every_template_is_valid(name):
    assert validate(render(name, **VALUES)) == []


@pytest.mark.parametrize("name", MARKDOWN)
@pytest.mark.parametrize("field", REQUIRED_FRONTMATTER)
def test_removing_a_required_field_fails_naming_it(name, field):
    text = render(name, **VALUES)
    broken = "\n".join(l for l in text.splitlines() if not l.startswith(f"{field}:"))
    messages = [str(p) for p in validate(broken)]
    assert any(f"'{field}'" in m for m in messages), messages


@pytest.mark.parametrize(
    "name,doc_type", [("work.md", "work"), ("decision.md", "decision")]
)
def test_removing_a_required_section_fails_naming_it(name, doc_type):
    text = render(name, **VALUES)
    for section in DOC_TYPES[doc_type].sections:
        broken = "\n".join(
            l for l in text.splitlines() if not (l.startswith("## ") and l.rstrip().endswith(section))
        )
        messages = [str(p) for p in validate(broken)]
        assert any(f"'{section}'" in m for m in messages), (section, messages)


def test_sections_out_of_order_fail():
    text = render("work.md", **VALUES).replace("## 2. Questions", "## 2. Questionsx")
    text = text.replace("## 5. Cost", "## 5. Cost\n\n## 6. Questions")
    assert any("out of order" in str(p) for p in validate(text))


def test_missing_summary_fails():
    text = render("doc.md", **VALUES).replace("> **Summary:**", "Summary:")
    assert any(p.rule == "summary" for p in validate(text))


def test_unknown_status_and_type_fail():
    text = render("work.md", **VALUES)
    assert any("status 'done'" in str(p) for p in validate(text.replace("status: planning", "status: done")))
    assert any("unknown type" in str(p) for p in validate(text.replace("type: work", "type: memo")))


def test_bad_date_fails():
    text = render("doc.md", **VALUES).replace("updated: 2026-11-16", "updated: yesterday")
    assert any("'updated' must be a date" in str(p) for p in validate(text))


def test_no_frontmatter_fails():
    assert [p.rule for p in validate("# Title\n")] == ["frontmatter"]


def test_unknown_template_is_refused():
    with pytest.raises(KeyError):
        render("memo.md", **VALUES)


@pytest.mark.parametrize(
    "replacement",
    ["status: [planning", "type: [work]", "status: {a: 1}", "type:\n  - work"],
)
def test_malformed_frontmatter_is_reported_not_raised(replacement):
    text = render("work.md", **VALUES)
    field = replacement.split(":")[0]
    broken = "\n".join(replacement if l.startswith(f"{field}:") else l for l in text.splitlines())
    problems = validate(broken)
    assert problems and all(p.rule in ("frontmatter", "summary", "sections") for p in problems)
    assert any(p.rule == "frontmatter" for p in problems)


@pytest.mark.parametrize(
    "transform",
    [
        lambda t: t.replace("\n", "\r\n"),
        lambda t: "﻿" + t,
        lambda t: t.replace("---\n", "--- \n", 2),
    ],
    ids=["crlf", "bom", "trailing-space"],
)
def test_frontmatter_tolerates_windows_and_editor_variants(transform):
    assert validate(transform(render("work.md", **VALUES))) == []


def test_frontmatter_closing_at_end_of_file():
    text = "---\ntype: review-list\nstatus: current\nupdated: 2026-11-16\n---"
    assert [p.rule for p in validate(text)] == ["summary"]


def test_datetime_is_not_a_date():
    text = render("doc.md", **VALUES).replace("updated: 2026-11-16", "updated: 2026-11-16 10:00:00")
    assert any("'updated' must be a date" in str(p) for p in validate(text))


@pytest.mark.parametrize("updated", ["2026-02-30", "2026-13-45"])
def test_impossible_date_is_reported_not_raised(updated):
    text = render("doc.md", **VALUES).replace("updated: 2026-11-16", f"updated: {updated}")
    assert [p.rule for p in validate(text)] == ["frontmatter"]


def test_deeply_nested_frontmatter_is_reported_not_raised():
    text = "---\na: " + "[" * 5000 + "\n---\n# T\n"
    assert [p.rule for p in validate(text)] == ["frontmatter"]


def test_alias_expansion_does_not_flood_messages():
    aliases = "a: &a [x,x,x,x,x,x,x,x,x,x]\n" + "".join(
        f"{c}: &{c} [*{p},*{p},*{p},*{p},*{p},*{p},*{p},*{p},*{p},*{p}]\n" for p, c in zip("abcde", "bcdef")
    )
    text = "---\ntype: work\n" + aliases + "status: *f\nupdated: 2026-11-16\n---\n# T\n"
    assert all(len(str(p)) < 200 for p in validate(text))
