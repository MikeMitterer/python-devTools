"""Ausgabe über CLITheme, wenn das Extra theme (mmit-cli-theme) installiert ist.

Eine Zeile besteht aus Teilen mit Rolle des Themes (head, key, val, hint, ok, warn, err, mark)
oder ohne Rolle. Ob Farben erscheinen, entscheidet die Konsole von CLITheme: nur im Terminal, nie
mit NO_COLOR oder TERM=dumb. Umbrochen wird nie (Output.write mit wrap=False): Eine Zeile wie
der Installationsbefehl von check bleibt zum Kopieren eine Zeile, das Terminal bricht sie nur
weich um.

finish schließt nach der Regel von CLITheme ab: eine Leerzeile auf jedem Strom, der Ausgabe
bekam. Parser ist dessen ArgumentParser, dessen Hilfe, Version und Fehler ebenso enden.
Ohne das Paket entsteht derselbe Text ohne Farben und ohne diesen Abschluss.
"""

import argparse
import sys
from functools import cache
from typing import TextIO

try:
    from cli_theme import ArgumentParser, Output
    from rich.text import Text
except ImportError:
    ArgumentParser = argparse.ArgumentParser
    Output = None

Parser = ArgumentParser
Part = tuple[str, str | None]


@cache
def themed() -> "Output | None":
    """Die Ausgabe nach dem gewählten Theme für den ganzen Lauf; None ohne das Extra theme."""
    return Output() if Output is not None else None


def emit(parts: list[Part], stream: TextIO | None = None) -> None:
    """Gibt eine Zeile aus Teilen aus, im Terminal in den Farben ihrer Rollen."""
    target = sys.stdout if stream is None else stream
    out = themed()
    if out is None:
        target.write("".join(text for text, _role in parts) + "\n")
        return
    line = Text()
    for text, role in parts:
        line.append(text, style=out.styles.get(role, "") if role else "")
    # wrap=False: nie hart umbrechen, damit etwa ein Befehl zum Kopieren eine Zeile bleibt.
    out.write(line, target, wrap=False)


def finish() -> None:
    """Schließt ab: eine Leerzeile je Strom mit Ausgabe (CLITheme); ohne das Paket nichts."""
    out = themed()
    if out is not None:
        out.finish()
