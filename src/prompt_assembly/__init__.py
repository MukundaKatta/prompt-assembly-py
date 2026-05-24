"""prompt-assembly: build multi-section LLM prompts from named parts.

System prompts are often composed of distinct sections: a role definition,
context, task instructions, output format rules.  A PromptAssembler keeps
those sections named and ordered, lets you swap individual parts between
calls, and renders them into a single string ready for the model.

Quick start::

    from prompt_assembly import PromptAssembler

    pa = PromptAssembler()
    pa.add_section("role", "You are a concise technical writer.")
    pa.add_section("context", "The user is debugging a Python script.")
    pa.add_section("task", "Explain the error message clearly.")
    pa.add_section("format", "Reply in three bullet points.")

    system_prompt = pa.render()

    # Swap just the task before the next turn
    pa.update_section("task", "Suggest a fix for the error.")
    system_prompt_v2 = pa.render()
"""

from .core import PromptAssembler

__all__ = ["PromptAssembler"]
__version__ = "0.1.0"
