# prompt-assembly

Build multi-section LLM prompts from named, ordered parts.

System prompts are often composed of distinct sections: a role definition, context, task instructions, output format rules. `PromptAssembler` keeps those sections named and ordered so you can swap individual parts between calls without rebuilding the whole string.

## Install

```bash
pip install prompt-assembly
```

## Quick start

```python
from prompt_assembly import PromptAssembler

pa = PromptAssembler()
pa.add_section("role", "You are a concise technical writer.")
pa.add_section("context", "The user is debugging a Python script.", prefix="## Context\n")
pa.add_section("task", "Explain the error message clearly.", prefix="## Task\n")
pa.add_section("format", "Reply in three bullet points.")

# Render all sections joined by \n\n (default)
system_prompt = pa.render()

# Render a subset
partial = pa.render(sections=["role", "task"])

# Custom separator
compact = pa.render(separator="\n---\n")

# Swap just the task
pa.update_section("task", "Suggest a fix for the error.")
system_prompt_v2 = pa.render()
```

## API

### `PromptAssembler(initial=None)`

- `add_section(name, content, *, prefix="", overwrite=False)` — add a named section; raises `ValueError` if the name already exists unless `overwrite=True`
- `update_section(name, content, *, prefix=None)` — update content/prefix of an existing section; raises `KeyError` if missing
- `remove(name)` — remove a section; raises `KeyError` if missing
- `clear()` — remove all sections
- `get(name, default=None)` — return content; raises `KeyError` if missing and no default given
- `get_prefix(name)` — return the section's prefix or `""`
- `section_names()` — list of names in insertion order
- `render(*, sections=None, separator="\n\n")` — render to string
- `to_dict()` / `from_dict(data)` — JSON-serialisable persistence

### Prefixes

Each section may have a prefix string (e.g. a Markdown heading) that is prepended at render time. The prefix is stored separately and is included in `to_dict()` / `from_dict()` round-trips.

```python
pa.add_section("context", "User is a Python developer.", prefix="## Context\n")
pa.render()
# "## Context\nUser is a Python developer."
```

## License

MIT
