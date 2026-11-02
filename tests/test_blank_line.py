"""T-10: Jede Ausgabe von devtools endet mit einer Leerzeile (über CLITheme, Extra theme);
Maschinenausgaben bleiben ohne."""

import pytest
from conftest import GIT_TOOLS


@pytest.mark.parametrize(
    "args", [(), ("-h",), ("--help",), ("upgrade", "-h"), ("check", "-h"), ("--version",)]
)
def test_help_and_version_end_with_blank_line(sandbox, args):
    """Hilfe in jeder Form und --version enden mit einer Leerzeile."""
    result, _ = sandbox.run(*args)
    assert result.returncode == 0, result.stderr
    assert result.stdout.endswith("\n\n") and not result.stdout.endswith("\n\n\n"), repr(
        result.stdout[-80:]
    )


@pytest.mark.parametrize("args", [("status",), ("install",), ("upgrade",), ("upgrade", "-n")])
def test_commands_end_with_one_blank_line(sandbox, args):
    """status, install und upgrade schließen ihre Ausgabe mit genau einer Leerzeile ab."""
    result, _ = sandbox.run(*args)
    assert result.stdout.endswith("\n\n") and not result.stdout.endswith("\n\n\n"), repr(
        result.stdout
    )


def test_errors_end_with_blank_line_on_stderr(sandbox):
    """Fehlermeldungen von check, unbekanntem Werkzeug und Argumenten enden auf stderr mit
    einer Leerzeile; stdout bleibt leer."""
    for args in (("check", "bashlib"), ("check", "gibtsnicht"), ("gibtsnicht",)):
        result, _ = sandbox.run(*args)
        assert result.returncode != 0, args
        assert result.stdout == "", (args, result.stdout)
        assert result.stderr.endswith("\n\n"), (args, repr(result.stderr))


def test_machine_output_stays_without_blank_line(sandbox):
    """command NAME gibt nur den Befehl aus; ein erfolgreiches check gibt nichts aus."""
    command, _ = sandbox.run("command", "projecttools")
    assert command.stdout == f"pipx install --force {GIT_TOOLS}@v0.3.2+261029.1600.c7bbd\n"
    checked, _ = sandbox.run("check", "projecttools")
    assert checked.returncode == 0 and checked.stdout == "" and checked.stderr == ""
