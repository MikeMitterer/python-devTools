"""Mindestversion: requires-python ist die Quelle; Doku und Makefile nennen dieselbe Version."""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
    "requires-python"
]
MINIMUM = REQUIRED.removeprefix(">=")


def test_minimum_is_python_3_14():
    """Vorgabe des Menschen (T-8): Python 3.14 als Mindestvoraussetzung."""
    assert REQUIRED == ">=3.14"


def test_docs_and_makefile_name_the_minimum():
    """Jede Versionsangabe in README, Entwicklerdoku und Makefile ist die aus requires-python."""
    named = {
        "README.md": r"Python (3\.\d+) or later",
        "README.de.md": r"Python (3\.\d+) oder neuer",
        "docs/development.md": r"Python (3\.\d+) oder neuer",
        "Makefile": r"PYTHON_BOOTSTRAP \?= python(3\.\d+)",
    }
    for name, pattern in named.items():
        found = re.findall(pattern, (ROOT / name).read_text(encoding="utf-8"))
        assert found, f"{name}: keine Versionsangabe"
        assert set(found) == {MINIMUM}, f"{name}: {found}, verlangt {MINIMUM}"
