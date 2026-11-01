"""Befehl devtools: Werkzeuge aus .dev-tools.conf.sh zeigen, installieren und prüfen."""

import argparse
import shlex
import sys
from importlib.metadata import version
from pathlib import Path

from mmit_devtools import pipx
from mmit_devtools.config import CONFIG_NAME, ConfigError, Tool, load_tools
from mmit_devtools.i18n import _
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
        hint = _("{state} → devtools install").format(state=result.text)
        line(tools, tool, hint if result.needed else result.text)
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
            text = _("pipx failed ({state}): {command}")
            line(tools, tool, text.format(state=result.text, command=shlex.join(tool.command())))
            sys.stderr.write(called.stderr[-2000:])
            continue
        line(tools, tool, done(tool, before, pipx.installed().get(tool.package)))
    return failed


def check(tool: Tool) -> int:
    """Mindestversion aus dem Tag; sonst Meldung samt Installationsbefehl und Exit 1."""
    found = pipx.installed().get(tool.package)
    if found is not None and satisfies(found, tool):
        return 0
    if found is None:
        text = _("✗ {label} missing (requires {minimum} or later): {command}")
    else:
        text = _("✗ {label} {version} is too old (requires {minimum} or later): {command}")
    values = {"label": tool.label, "minimum": tool.minimum, "command": shlex.join(tool.command())}
    sys.stderr.write(f"  {text.format(version=found and found.version, **values)}\n")
    return 1


def parser() -> argparse.ArgumentParser:
    """Argumente: status, install, check NAME, command NAME, --config und --version."""
    result = argparse.ArgumentParser(
        prog="devtools",
        description=_(
            "Show, install and check the development tools from {config} with pipx."
        ).format(config=CONFIG_NAME),
    )
    result.add_argument(
        "-f",
        "--config",
        metavar=_("FILE"),
        type=Path,
        default=Path(CONFIG_NAME),
        help=_("another config instead of {config} in the current folder").format(
            config=CONFIG_NAME
        ),
    )
    result.add_argument("--version", action="version", version=f"%(prog)s {version(PACKAGE)}")
    commands = result.add_subparsers(dest="command", metavar=_("COMMAND"))
    commands.add_parser("status", help=_("show state and source of each tool, install nothing"))
    commands.add_parser("install", help=_("bring each tool to its source and tag"))
    for name, text in (
        ("check", _("check the minimum version; otherwise name the command, exit 1")),
        ("command", _("print the install command")),
    ):
        commands.add_parser(name, help=text).add_argument("name", metavar=_("NAME"))
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
            text = _("✗ Unknown tool {name}; known: {known}")
            sys.stderr.write(
                f"  {text.format(name=repr(arguments.name), known=', '.join(named))}\n"
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
