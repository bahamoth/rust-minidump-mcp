"""Shared helpers for *rust_minidump_mcp* tool implementations.

This module purposefully keeps a **tiny** footprint – just enough to be useful
for the current tooling needs without pulling in heavy dependencies or
replicating FastMCP internals.  Keeping it small also means unit-tests can run
quickly inside the execution sandbox.
"""

from __future__ import annotations

import asyncio
import shutil
import sys
from pathlib import Path
from typing import Iterable


class ToolExecutionError(RuntimeError):
    """Raised when the wrapped CLI tool fails (non-zero exit-status)."""


async def run_subprocess(
    cmd: Iterable[str | Path], *, capture_output: bool = True, timeout: float | None = None
) -> str:  # noqa: D401 – helper wrapper
    """Run *cmd* asynchronously and return its **stdout** as a *string*.

    Parameters
    ----------
    cmd:
        Sequence of command-line parts.  ``Path`` objects are converted to
        ``str`` automatically for convenience.
    capture_output:
        When *True* (the default) the function captures ``stdout``/**stderr``.
        Otherwise the child process inherits the parent file-descriptors which
        is useful for manual debugging.
    timeout:
        Optional maximum runtime in *seconds*.  The subprocess is **forcefully
        killed** if the limit is exceeded and :class:`asyncio.TimeoutError` is
        re-raised to the caller.
    """

    # Ensure *cmd* is fully stringified – ``asyncio.create_subprocess_exec``
    # will otherwise error on ``Path`` entries.
    str_cmd = [str(part) for part in cmd]

    # On Windows the default event-loop policy does not support ``subprocess``
    # transports.  Emit a helpful error early so the caller can react.
    if sys.platform == "win32":
        raise RuntimeError("Asynchronous subprocess execution is not supported on Windows.")

    # Spawn the child process.
    proc = await asyncio.create_subprocess_exec(
        *str_cmd,
        stdout=asyncio.subprocess.PIPE if capture_output else None,
        stderr=asyncio.subprocess.PIPE if capture_output else None,
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
    except asyncio.TimeoutError:  # pragma: no cover – unlikely in unit tests
        proc.kill()
        raise  # Re-raise for caller

    # ``stdout``/``stderr`` can be *None* when *capture_output* is ``False`` –
    # guard against ``AttributeError`` when decoding.
    out_text = stdout.decode() if stdout else ""
    err_text = stderr.decode() if stderr else ""

    if proc.returncode != 0:
        raise ToolExecutionError(f"Command {' '.join(str_cmd)} failed with exit-code {proc.returncode}\n{err_text}")

    return out_text


def which(cmd: str) -> str | None:  # noqa: D401 – thin wrapper
    """Return the absolute path to *cmd* or *None* when not found on *PATH*."""

    return shutil.which(cmd)
