"""Utilities for reading and writing prompt files.

These helper functions centralise how prompt files are loaded and saved.  All
prompts are expected to be stored under the `prompts/` directory.
"""

from pathlib import Path
from typing import Union


def read_prompt(path: Union[str, Path]) -> str:
    """Read the contents of a prompt file.

    Args:
        path: Path to the markdown prompt file.

    Returns:
        The file contents as a UTF‑8 string.
    """
    p = Path(path)
    return p.read_text(encoding='utf-8')


def write_prompt(path: Union[str, Path], content: str) -> None:
    """Write content to a prompt file, creating directories as needed.

    Args:
        path: Target file path.
        content: Markdown content to be written.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')