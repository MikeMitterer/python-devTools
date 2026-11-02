"""Farbige Ausgabe über CLITheme, wenn das Extra theme (mmit-cli-theme) installiert ist.

Eine Zeile besteht aus Teilen mit Rolle des Themes (head, key, val, hint, ok, warn, err, mark)
oder ohne Rolle. Ob Farben erscheinen, entscheidet die Konsole von CLITheme: nur im Terminal, nie
mit NO_COLOR oder TERM=dumb. Umbrochen wird nie: Eine Zeile wie der Installationsbefehl von check
bleibt zum Kopieren eine Zeile, das Terminal bricht sie nur weich um. Ohne das Paket entsteht
derselbe Text ohne Farben.
"""

import sys
from functools import cache
from typing import TextIO

try:
    from cli_theme import styles
    from cli_theme.output import console_for
    from rich.text import Text
except ImportError:
    styles = None

Part = tuple[str, str | None]


@cache
def theme_styles() -> dict[str, str] | None:
    """rich-Stil je Rolle des gewählten Themes; None ohne das Extra theme."""
    return styles() if styles is not None else None


def emit(parts: list[Part], stream: TextIO | None = None) -> None:
    """Gibt eine Zeile aus Teilen aus, im Terminal in den Farben ihrer Rollen."""
    target = sys.stdout if stream is None else stream
    roles = theme_styles()
    if roles is None:
        target.write("".join(text for text, _role in parts) + "\n")
        return
    line = Text()
    for text, role in parts:
        line.append(text, style=roles.get(role, "") if role else "")
    console_for(target).print(line, crop=False, overflow="ignore")
