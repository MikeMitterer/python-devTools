"""Farben über CLITheme: nur im Terminal und ohne NO_COLOR; ohne das Extra theme reiner Text."""

import io
import re

import pytest
from cli_theme import install_themes

from mmit_devtools import style

ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
PARTS = [("  ", None), ("BashLib", "key"), ("  ", None), ("0.1.0, wanted 0.2.0", "warn")]
PLAIN = "  BashLib  0.1.0, wanted 0.2.0\n"


class Terminal(io.StringIO):
    """Strom, der sich als Terminal ausgibt."""

    def isatty(self) -> bool:
        return True


@pytest.fixture
def theme(tmp_path, monkeypatch):
    """Theme classic in einem eigenen Konfigurationsordner, ein Farbterminal, kein NO_COLOR."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("CLI_THEME", raising=False)
    install_themes()
    style.themed.cache_clear()
    yield
    style.themed.cache_clear()


def test_terminal_shows_theme_colors_around_the_same_text(theme):
    """Im Terminal färbt die Rolle warn den Zustand (classic: 208), key die Bezeichnung (33)."""
    stream = Terminal()
    style.emit(PARTS, stream)
    shown = stream.getvalue()
    assert "38;5;208" in shown and "38;5;33" in shown, repr(shown)
    assert ESCAPE.sub("", shown) == PLAIN


def test_pipe_and_no_color_give_plain_text(theme, monkeypatch):
    """In einer Pipe und mit NO_COLOR im Terminal: derselbe Text ohne Escape-Codes."""
    piped = io.StringIO()
    style.emit(PARTS, piped)
    assert piped.getvalue() == PLAIN

    monkeypatch.setenv("NO_COLOR", "")
    stream = Terminal()
    style.emit(PARTS, stream)
    assert stream.getvalue() == PLAIN


def test_without_cli_theme_output_stays_plain(theme, monkeypatch):
    """Ohne das Extra theme (kein mmit-cli-theme): reiner Text, auch im Terminal."""
    monkeypatch.setattr(style, "Output", None)
    style.themed.cache_clear()
    stream = Terminal()
    style.emit(PARTS, stream)
    assert stream.getvalue() == PLAIN


LONG = [("  ", None), ("✗ BashLib 0.1.0 is too old: pipx install --force " + "x" * 120, "err")]


@pytest.mark.parametrize("no_color", [False, True])
def test_long_line_stays_one_line_in_narrow_terminal(theme, monkeypatch, no_color):
    """R1-F1: Ein Befehl zum Kopieren bleibt eine Zeile, auch im schmalen Terminal; das
    Terminal bricht nur weich um, devtools fügt keinen Zeilenumbruch ein."""
    monkeypatch.setenv("COLUMNS", "40")
    if no_color:
        monkeypatch.setenv("NO_COLOR", "1")
    stream = Terminal()
    style.emit(LONG, stream)
    assert ESCAPE.sub("", stream.getvalue()) == "".join(text for text, _ in LONG) + "\n"


def test_finish_ends_each_written_stream_with_one_blank_line(theme):
    """T-10: Der Abschluss von CLITheme setzt je Strom mit Ausgabe genau eine Leerzeile."""
    out, err, silent = io.StringIO(), io.StringIO(), io.StringIO()
    style.emit(PARTS, out)
    style.emit(PARTS, out)
    style.emit(PARTS, err)
    style.finish()
    assert out.getvalue() == PLAIN * 2 + "\n"
    assert err.getvalue() == PLAIN + "\n"
    assert silent.getvalue() == ""
    style.finish()
    assert out.getvalue() == PLAIN * 2 + "\n", "ein zweiter Abschluss ohne neue Ausgabe"


def test_emit_writes_through_cli_theme_without_wrapping(theme, monkeypatch):
    """T-11: emit schreibt über Output.write(..., wrap=False) von CLITheme und fasst dessen
    Vormerkung für finish nicht selbst an."""
    out = style.themed()
    seen = []
    original = type(out).write

    def spy(self, text, stream=None, hang=0, wrap=True):
        seen.append(wrap)
        original(self, text, stream, hang, wrap)

    monkeypatch.setattr(type(out), "write", spy)
    stream = io.StringIO()
    style.emit(PARTS, stream)
    assert seen == [False]
    assert stream.getvalue() == PLAIN
