"""Befehl devtools: Werkzeuge aus .dev-tools.conf.sh zeigen, installieren und prüfen."""

import argparse
import shlex
import sys
from importlib.metadata import version
from pathlib import Path

from mmit_devtools import pipx
from mmit_devtools.config import CONFIG_NAME, ConfigError, Tool, load_tools
from mmit_devtools.sync import done, plan, satisfies

PACKAGE = "mmit-devtools"


def line(tools: list[Tool], tool: Tool, text: str) -> None:
    """Eine Zeile je Werkzeug; die Beschriftungen aller Werkzeuge stehen bündig."""
    width = max(len(each.label) for each in tools)
    print(f"  {tool.label:<{width}}  {text}")


def status(tools: list[Tool]) -> int:
    """Je Werkzeug Stand und Quelle; installiert nichts."""
    found = pipx.installed()
    for tool in tools:
        result = plan(tool, found.get(tool.package))
        line(tools, tool, result.text + (" → devtools install" if result.needed else ""))
    return 0


def install(tools: list[Tool]) -> int:
    """Bringt jedes Werkzeug auf Quelle und Tag; meldet je Werkzeug, was geschah."""
    found, failed = pipx.installed(), 0
    for tool in tools:
        before = found.get(tool.package)
        result = plan(tool, before)
        if not result.needed:
            line(tools, tool, result.text)
            continue
        called = pipx.run(tool.command())
        if called.returncode:
            failed = 1
            line(tools, tool, f"pipx scheiterte ({result.text}): {shlex.join(tool.command())}")
            sys.stderr.write(called.stderr[-2000:])
            continue
        line(tools, tool, done(tool, before, pipx.installed().get(tool.package)))
    return failed


def check(tool: Tool) -> int:
    """Mindestversion aus dem Tag; sonst Meldung samt Installationsbefehl und Exit 1."""
    found = pipx.installed().get(tool.package)
    if found is not None and satisfies(found, tool):
        return 0
    problem = "fehlt" if found is None else f"{found.version} ist zu alt"
    sys.stderr.write(
        f"  ✗ {tool.label} {problem} (verlangt ab {tool.minimum}): {shlex.join(tool.command())}\n"
    )
    return 1


def parser() -> argparse.ArgumentParser:
    """Argumente: status, install, check NAME, command NAME, --config und --version."""
    result = argparse.ArgumentParser(
        prog="devtools",
        description=f"Entwicklungswerkzeuge aus {CONFIG_NAME} über pipx zeigen, "
        "installieren und prüfen.",
    )
    result.add_argument(
        "-f",
        "--config",
        metavar="DATEI",
        type=Path,
        default=Path(CONFIG_NAME),
        help=f"andere Config statt {CONFIG_NAME} im aktuellen Ordner",
    )
    result.add_argument("--version", action="version", version=f"%(prog)s {version(PACKAGE)}")
    commands = result.add_subparsers(dest="command", metavar="BEFEHL")
    commands.add_parser("status", help="je Werkzeug Stand und Quelle zeigen, nichts installieren")
    commands.add_parser("install", help="jedes Werkzeug auf Quelle und Tag bringen")
    for name, text in (
        ("check", "Mindestversion prüfen; sonst Befehl nennen, Exit 1"),
        ("command", "Installationsbefehl ausgeben"),
    ):
        commands.add_parser(name, help=text).add_argument("name", metavar="NAME")
    return result


def main(argv: list[str] | None = None) -> int:
    """Einstieg des Befehls devtools; Fehler in Config oder pipx enden mit Exit 1."""
    arguments = parser().parse_args(argv)
    if arguments.command is None:
        parser().print_help()
        return 0
    try:
        tools = load_tools(arguments.config)
        if arguments.command == "status":
            return status(tools)
        if arguments.command == "install":
            return install(tools)
        named = {tool.name: tool for tool in tools}
        tool = named.get(arguments.name.lower())
        if tool is None:
            sys.stderr.write(
                f"  ✗ Unbekanntes Werkzeug {arguments.name!r}; bekannt: {', '.join(named)}\n"
            )
            return 2
        if arguments.command == "command":
            print(shlex.join(tool.command()))
            return 0
        return check(tool)
    except (ConfigError, pipx.PipxError) as error:
        sys.stderr.write(f"  ✗ {error}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
