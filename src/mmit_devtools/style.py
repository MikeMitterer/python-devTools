"""Farbige Ausgabe über CLITheme, wenn das Extra theme (mmit-cli-theme) installiert ist.

Eine Zeile besteht aus Teilen mit Rolle des Themes (head, key, val, hint, ok, warn, err, mark)
oder ohne Rolle. Ob Farben erscheinen, entscheidet cli_theme.Output: nur im Terminal, nie mit
NO_COLOR oder TERM=dumb. Ohne das Paket entsteht derselbe Text ohne Farben, wie vor CLITheme.
"""

import sys
from functools import cache
from typing import TextIO

try:
    from cli_theme import Output
    from rich.text import Text
except ImportError:
    Output = None

Part = tuple[str, str | None]


@cache
def themed() -> "Output | None":
    """Die Ausgabe nach dem gewählten Theme; None ohne das Extra theme."""
    return Output() if Output is not None else None


def emit(parts: list[Part], stream: TextIO | None = None, hang: int = 0) -> None:
    """Gibt eine Zeile aus Teilen aus; hang ist die Spalte, in der umbrochene Zeilen beginnen."""
    target = sys.stdout if stream is None else stream
    out = themed()
    if out is None:
        target.write("".join(text for text, _role in parts) + "\n")
        return
    line = Text()
    for text, role in parts:
        line.append(text, style=out.styles.get(role, "") if role else "")
    out.write(line, target, hang=hang)
