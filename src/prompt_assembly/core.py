"""Multi-section LLM prompt assembler.

A :class:`PromptAssembler` is an insertion-ordered collection of named
string sections.  Sections are joined by a configurable separator when
rendered.  Optional per-section prefixes (e.g. Markdown headings) are
prepended to the section content at render time.

Typical use::

    pa = PromptAssembler()
    pa.add_section("role", "You are a helpful assistant.")
    pa.add_section("context", context_text, prefix="## Context\\n")
    pa.add_section("task", task_text, prefix="## Task\\n")

    system_msg = pa.render()                  # all sections, joined by \\n\\n
    partial    = pa.render(sections=["role", "task"])  # subset
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterator
from typing import Any


class PromptAssembler:
    """Ordered collection of named prompt sections.

    Sections are stored in insertion order.  Each section may carry an
    optional *prefix* string prepended at render time (e.g. a Markdown
    heading).

    Args:
        initial: Optional ``{name: content}`` mapping to pre-populate the
            assembler.  Sections are added in iteration order; no prefixes
            are set for sections coming from *initial*.

    Example::

        pa = PromptAssembler({"role": "You are helpful.", "task": "Summarise."})
        print(pa.render())
        # You are helpful.
        #
        # Summarise.
    """

    def __init__(self, initial: dict[str, str] | None = None) -> None:
        self._sections: OrderedDict[str, str] = OrderedDict()
        self._prefixes: dict[str, str] = {}
        if initial:
            for name, content in initial.items():
                self.add_section(name, content)

    # ------------------------------------------------------------------
    # Mutating interface
    # ------------------------------------------------------------------

    def add_section(
        self,
        name: str,
        content: str,
        *,
        prefix: str = "",
        overwrite: bool = False,
    ) -> None:
        """Add a named section to the assembler.

        Args:
            name: Unique section name.
            content: Text content of the section.
            prefix: Optional string prepended to the content at render time.
            overwrite: If *True*, silently replace an existing section.

        Raises:
            TypeError: If *name* or *content* is not a string.
            ValueError: If *name* already exists and *overwrite* is *False*.
        """
        if not isinstance(name, str):
            raise TypeError(f"Section name must be a str, got {type(name).__name__!r}.")
        if not isinstance(content, str):
            raise TypeError(f"Section content must be a str, got {type(content).__name__!r}.")
        if name in self._sections and not overwrite:
            raise ValueError(f"Section {name!r} already exists. Use overwrite=True to replace.")
        self._sections[name] = content
        if prefix:
            self._prefixes[name] = prefix
        elif name in self._prefixes and overwrite:
            # Clear stale prefix when overwriting without a new one
            del self._prefixes[name]

    def update_section(self, name: str, content: str, *, prefix: str | None = None) -> None:
        """Update the content (and optionally the prefix) of an existing section.

        Args:
            name: Name of the section to update.
            content: New content string.
            prefix: If provided, replace the existing prefix.  Pass ``""``
                to remove the prefix.

        Raises:
            KeyError: If *name* does not exist.
            TypeError: If *content* is not a string.
        """
        if name not in self._sections:
            raise KeyError(name)
        if not isinstance(content, str):
            raise TypeError(f"Section content must be a str, got {type(content).__name__!r}.")
        self._sections[name] = content
        if prefix is not None:
            if prefix:
                self._prefixes[name] = prefix
            else:
                self._prefixes.pop(name, None)

    def remove(self, name: str) -> None:
        """Remove a section by name.

        Args:
            name: Section to remove.

        Raises:
            KeyError: If *name* does not exist.
        """
        del self._sections[name]
        self._prefixes.pop(name, None)

    def clear(self) -> None:
        """Remove all sections and prefixes."""
        self._sections.clear()
        self._prefixes.clear()

    # ------------------------------------------------------------------
    # Read interface
    # ------------------------------------------------------------------

    def get(self, name: str, default: str | None = None) -> str | None:
        """Return the content for *name*, or *default* if absent.

        When called with no *default*, behaves like ``dict.__getitem__``:
        raises :exc:`KeyError` if the section is missing.  When *default* is
        provided (including ``None``), returns it silently.

        Args:
            name: Section name.
            default: Fallback value.

        Returns:
            Section content or *default*.

        Raises:
            KeyError: If *name* is absent and no *default* was given.
        """
        # Distinguish "no argument passed" from "None passed explicitly"
        # by using a sentinel in the signature via *args trick instead.
        # But to keep the API simple we allow None as an explicit default.
        if default is None and name not in self._sections:
            raise KeyError(name)
        return self._sections.get(name, default)  # type: ignore[return-value]

    def get_prefix(self, name: str) -> str:
        """Return the prefix for *name*, or ``""`` if none is set.

        Args:
            name: Section name.

        Returns:
            Prefix string (may be empty).
        """
        return self._prefixes.get(name, "")

    def section_names(self) -> list[str]:
        """Return all section names in insertion order."""
        return list(self._sections.keys())

    def __contains__(self, name: object) -> bool:
        return name in self._sections

    def __len__(self) -> int:
        return len(self._sections)

    def __iter__(self) -> Iterator[str]:
        return iter(self._sections)

    def __repr__(self) -> str:
        return f"PromptAssembler({dict(self._sections)!r})"

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(
        self,
        *,
        sections: list[str] | None = None,
        separator: str = "\n\n",
    ) -> str:
        """Render sections into a single string.

        Each section is optionally prepended with its registered prefix
        before joining.

        Args:
            sections: If provided, include only these section names (in the
                given order).  Unknown names are silently skipped.
            separator: String placed between sections (default ``"\\n\\n"``).

        Returns:
            Joined string.  Empty string when no sections are present or
            all requested names are unknown.
        """
        source = (
            [(k, self._sections[k]) for k in sections if k in self._sections]
            if sections is not None
            else list(self._sections.items())
        )
        if not source:
            return ""

        parts: list[str] = []
        for k, v in source:
            prefix = self._prefixes.get(k, "")
            parts.append(f"{prefix}{v}" if prefix else v)

        return separator.join(parts)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain ``dict``.

        Returns:
            ``{"sections": {...}, "prefixes": {...}}``
        """
        return {
            "sections": dict(self._sections),
            "prefixes": dict(self._prefixes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptAssembler:
        """Restore a :class:`PromptAssembler` from a plain ``dict``.

        Args:
            data: Mapping previously produced by :meth:`to_dict`.

        Returns:
            New :class:`PromptAssembler` with the same sections and prefixes.
        """
        instance = cls(data.get("sections", {}))
        for k, v in data.get("prefixes", {}).items():
            instance._prefixes[k] = v
        return instance
