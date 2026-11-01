"""Versionen lesen und vergleichen: SemVer-Teil eines Tags, Version einer Arbeitskopie."""

import re
import tomllib
from pathlib import Path

SEMVER = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def semver(text: str) -> str | None:
    """1.2.3 aus einem Tag wie v1.2.3+261031.2038.b22f0; None ohne SemVer-Teil."""
    match = SEMVER.search(text)
    return match.group(0) if match else None


def as_tuple(version: str | None) -> tuple[int, ...]:
    """Version zum Vergleichen; ohne lesbare Version ganz unten."""
    match = SEMVER.search(version or "")
    return tuple(int(part) for part in match.groups()) if match else (-1,)


def working_copy_version(path: Path) -> str | None:
    """Version aus pyproject.toml einer Arbeitskopie.

    pipx friert bei pipx install -e die Paketversion beim Installieren ein; die gültige Version
    einer bearbeitbaren Arbeitskopie steht deshalb nur in ihrer pyproject.toml.
    """
    try:
        text = (path / "pyproject.toml").read_text(encoding="utf-8")
        return str(tomllib.loads(text)["project"]["version"])
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError):
        return None
