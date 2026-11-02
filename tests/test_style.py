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
