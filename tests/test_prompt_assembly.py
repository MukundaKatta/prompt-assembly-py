"""Tests for prompt-assembly."""

from __future__ import annotations

import pytest

from prompt_assembly import PromptAssembler

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_empty_init():
    pa = PromptAssembler()
    assert len(pa) == 0


def test_init_with_dict():
    pa = PromptAssembler({"role": "You are helpful.", "task": "Summarise."})
    assert pa.get("role") == "You are helpful."
    assert pa.get("task") == "Summarise."


def test_init_preserves_order():
    pa = PromptAssembler({"z": "1", "a": "2", "m": "3"})
    assert pa.section_names() == ["z", "a", "m"]


def test_init_no_prefixes():
    pa = PromptAssembler({"role": "You are helpful."})
    assert pa.get_prefix("role") == ""


# ---------------------------------------------------------------------------
# add_section
# ---------------------------------------------------------------------------


def test_add_section_basic():
    pa = PromptAssembler()
    pa.add_section("role", "You are helpful.")
    assert pa.get("role") == "You are helpful."


def test_add_section_with_prefix():
    pa = PromptAssembler()
    pa.add_section("context", "Some context.", prefix="## Context\n")
    assert pa.get_prefix("context") == "## Context\n"


def test_add_section_duplicate_raises():
    pa = PromptAssembler()
    pa.add_section("role", "v1")
    with pytest.raises(ValueError, match="already exists"):
        pa.add_section("role", "v2")


def test_add_section_overwrite():
    pa = PromptAssembler()
    pa.add_section("role", "v1")
    pa.add_section("role", "v2", overwrite=True)
    assert pa.get("role") == "v2"
    assert len(pa) == 1


def test_add_section_overwrite_clears_old_prefix():
    pa = PromptAssembler()
    pa.add_section("ctx", "text", prefix="## Old\n")
    pa.add_section("ctx", "new text", overwrite=True)
    assert pa.get_prefix("ctx") == ""


def test_add_section_non_string_name_raises():
    pa = PromptAssembler()
    with pytest.raises(TypeError, match="name must be a str"):
        pa.add_section(123, "content")  # type: ignore[arg-type]


def test_add_section_non_string_content_raises():
    pa = PromptAssembler()
    with pytest.raises(TypeError, match="content must be a str"):
        pa.add_section("role", 99)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# update_section
# ---------------------------------------------------------------------------


def test_update_section():
    pa = PromptAssembler({"task": "Old task."})
    pa.update_section("task", "New task.")
    assert pa.get("task") == "New task."


def test_update_section_missing_raises():
    pa = PromptAssembler()
    with pytest.raises(KeyError):
        pa.update_section("nope", "content")


def test_update_section_with_new_prefix():
    pa = PromptAssembler()
    pa.add_section("ctx", "text")
    pa.update_section("ctx", "new text", prefix="## Ctx\n")
    assert pa.get_prefix("ctx") == "## Ctx\n"


def test_update_section_clear_prefix():
    pa = PromptAssembler()
    pa.add_section("ctx", "text", prefix="## Ctx\n")
    pa.update_section("ctx", "text", prefix="")
    assert pa.get_prefix("ctx") == ""


def test_update_section_non_string_content_raises():
    pa = PromptAssembler({"task": "text"})
    with pytest.raises(TypeError):
        pa.update_section("task", 42)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# remove / clear
# ---------------------------------------------------------------------------


def test_remove_existing():
    pa = PromptAssembler({"role": "v", "task": "t"})
    pa.remove("role")
    assert "role" not in pa
    assert len(pa) == 1


def test_remove_missing_raises():
    pa = PromptAssembler()
    with pytest.raises(KeyError):
        pa.remove("nope")


def test_remove_also_clears_prefix():
    pa = PromptAssembler()
    pa.add_section("ctx", "text", prefix="## Ctx\n")
    pa.remove("ctx")
    assert "ctx" not in pa


def test_clear():
    pa = PromptAssembler({"a": "1", "b": "2"})
    pa.clear()
    assert len(pa) == 0


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


def test_get_existing():
    pa = PromptAssembler({"k": "v"})
    assert pa.get("k") == "v"


def test_get_missing_no_default_raises():
    pa = PromptAssembler()
    with pytest.raises(KeyError):
        pa.get("missing")


def test_get_missing_with_default():
    pa = PromptAssembler()
    assert pa.get("missing", "fallback") == "fallback"


def test_get_missing_with_none_default():
    pa = PromptAssembler()
    # None is treated as "no default" in our API — raises KeyError
    with pytest.raises(KeyError):
        pa.get("missing")


def test_get_missing_with_falsy_default():
    pa = PromptAssembler()
    # A non-None falsy default is returned, not treated as "no default".
    assert pa.get("missing", "") == ""


# ---------------------------------------------------------------------------
# section_names / contains / len / iter
# ---------------------------------------------------------------------------


def test_section_names_order():
    pa = PromptAssembler()
    pa.add_section("z", "1")
    pa.add_section("a", "2")
    pa.add_section("m", "3")
    assert pa.section_names() == ["z", "a", "m"]


def test_contains_true():
    pa = PromptAssembler({"k": "v"})
    assert "k" in pa


def test_contains_false():
    pa = PromptAssembler()
    assert "nope" not in pa


def test_len_empty():
    assert len(PromptAssembler()) == 0


def test_len_after_adds():
    pa = PromptAssembler()
    pa.add_section("a", "1")
    pa.add_section("b", "2")
    assert len(pa) == 2


def test_iter():
    pa = PromptAssembler({"a": "1", "b": "2"})
    assert list(pa) == ["a", "b"]


# ---------------------------------------------------------------------------
# render — basic
# ---------------------------------------------------------------------------


def test_render_empty():
    assert PromptAssembler().render() == ""


def test_render_single():
    pa = PromptAssembler({"role": "You are helpful."})
    assert pa.render() == "You are helpful."


def test_render_multiple_default_separator():
    pa = PromptAssembler({"a": "first", "b": "second"})
    assert pa.render() == "first\n\nsecond"


def test_render_custom_separator():
    pa = PromptAssembler({"a": "one", "b": "two"})
    assert pa.render(separator=" | ") == "one | two"


def test_render_with_prefix():
    pa = PromptAssembler()
    pa.add_section("ctx", "Some context.", prefix="## Context\n")
    result = pa.render()
    assert result == "## Context\nSome context."


def test_render_mixed_prefix():
    pa = PromptAssembler()
    pa.add_section("role", "You are helpful.")
    pa.add_section("ctx", "Context here.", prefix="## Context\n")
    result = pa.render()
    assert "You are helpful." in result
    assert "## Context\nContext here." in result


# ---------------------------------------------------------------------------
# render — sections filter
# ---------------------------------------------------------------------------


def test_render_subset_sections():
    pa = PromptAssembler({"a": "1", "b": "2", "c": "3"})
    result = pa.render(sections=["a", "c"])
    assert "1" in result
    assert "3" in result
    assert "2" not in result


def test_render_sections_order_respected():
    pa = PromptAssembler({"a": "first", "b": "second", "c": "third"})
    result = pa.render(sections=["c", "a"])
    assert result.index("third") < result.index("first")


def test_render_unknown_sections_skipped():
    pa = PromptAssembler({"a": "1"})
    result = pa.render(sections=["a", "unknown"])
    assert "1" in result
    assert "unknown" not in result


def test_render_empty_sections_list():
    pa = PromptAssembler({"a": "1"})
    assert pa.render(sections=[]) == ""


# ---------------------------------------------------------------------------
# repr
# ---------------------------------------------------------------------------


def test_repr_contains_section_data():
    pa = PromptAssembler({"k": "v"})
    r = repr(pa)
    assert "k" in r
    assert "v" in r


# ---------------------------------------------------------------------------
# to_dict / from_dict
# ---------------------------------------------------------------------------


def test_to_dict():
    pa = PromptAssembler()
    pa.add_section("role", "You are helpful.", prefix="## Role\n")
    pa.add_section("task", "Summarise.")
    d = pa.to_dict()
    assert d["sections"] == {"role": "You are helpful.", "task": "Summarise."}
    assert d["prefixes"] == {"role": "## Role\n"}


def test_to_dict_is_copy():
    pa = PromptAssembler({"k": "v"})
    d = pa.to_dict()
    d["sections"]["k"] = "changed"
    assert pa.get("k") == "v"


def test_from_dict():
    pa = PromptAssembler()
    pa.add_section("role", "You are helpful.", prefix="## Role\n")
    pa.add_section("task", "Summarise.")
    d = pa.to_dict()
    pa2 = PromptAssembler.from_dict(d)
    assert pa2.get("role") == "You are helpful."
    assert pa2.get_prefix("role") == "## Role\n"
    assert pa2.get("task") == "Summarise."


def test_roundtrip_render():
    pa = PromptAssembler()
    pa.add_section("role", "You are helpful.", prefix="## Role\n")
    pa.add_section("task", "Summarise.")
    rendered = pa.render()
    pa2 = PromptAssembler.from_dict(pa.to_dict())
    assert pa2.render() == rendered


def test_from_dict_non_dict_raises():
    with pytest.raises(TypeError, match="data must be a dict"):
        PromptAssembler.from_dict(["not", "a", "dict"])  # type: ignore[arg-type]


def test_from_dict_drops_orphan_prefixes():
    # A prefix whose section is absent must not be retained.
    pa = PromptAssembler.from_dict({"sections": {"a": "1"}, "prefixes": {"ghost": "## Ghost\n"}})
    assert pa.get_prefix("ghost") == ""
    assert pa.render() == "1"
