"""Shared utilities for Temporal activities."""

from __future__ import annotations

import io
import re
from contextlib import redirect_stdout

from dspy.clients.base_lm import GLOBAL_HISTORY
from dspy.utils.inspect_history import pretty_print_history

_ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def capture_llm_history(n: int = 1) -> str:
    """Return the most recent DSPy LM interaction history as plain text.

    Parameters
    ----------
    n: int, optional
        Number of history entries to include, defaults to 1 (most recent only).
    """
    if not GLOBAL_HISTORY:
        return ""

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        pretty_print_history(GLOBAL_HISTORY, n=n)

    history_output = buffer.getvalue()
    return _ANSI_ESCAPE_RE.sub("", history_output).strip()
