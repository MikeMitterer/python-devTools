"""Befehl devtools: Werkzeuge aus .dev-tools.conf.sh zeigen, installieren, aktualisieren, prüfen."""

import argparse
import shlex
import sys
from importlib.metadata import version
from pathlib import Path

from mmit_devtools import git, pipx
from mmit_devtools.config import (
    CONFIG_NAME,
    AnyPin,
    ConfigError,
    Pin,
    Tool,
    load_pins,
    load_tools,
    write_tags,
)
from mmit_devtools.i18n import _
from mmit_devtools.pipx import Installed
from mmit_devtools.sync import done, plan, satisfies, upgraded
from mmit_devtools.versions import semver

PACKAGE = "mmit-devtools"


class UnknownTool(Exception):
    """NAME nennt kein Werkzeug der Config; der Text nennt die bekannten."""


def line(tools: list[Pin], tool: Pin, text: str) -> None:
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


def ordered(tools: list[AnyPin]) -> list[AnyPin]:
    """devtools selbst zuletzt: pipx ersetzt dabei die venv, aus der dieser Lauf kommt."""
    return sorted(tools, key=lambda tool: isinstance(tool, Tool) and tool.package == PACKAGE)


def bring(tools: list[Pin], tool: Tool, found: dict[str, Installed]) -> bool:
    """Bringt ein Werkzeug auf Quelle und Tag, meldet, was geschah; False, wenn pipx scheitert."""
    before = found.get(tool.package)
    result = plan(tool, before)
    if not result.needed:
        line(tools, tool, result.text)
        return True
    called = pipx.run(tool.command())
    if called.returncode:
        text = _("pipx failed ({state}): {command}")
        line(tools, tool, text.format(state=result.text, command=shlex.join(tool.command())))
        sys.stderr.write(called.stderr[-2000:])
        return False
    line(tools, tool, done(tool, before, pipx.installed().get(tool.package)))
    return True


def install(tools: list[Tool]) -> int:
    """Bringt jedes Werkzeug auf Quelle und Tag; meldet je Werkzeug, was geschah."""
    found = pipx.installed()
    results = [bring(tools, tool, found) for tool in ordered(tools)]
    return 0 if all(results) else 1


def newest_tags(tools: list[Pin]) -> dict[str, str | git.GitError]:
    """Je Werkzeug der neueste Release-Tag seiner Quelle oder der Fehler, der ihn verhindert."""
    result: dict[str, str | git.GitError] = {}
    for tool in tools:
        try:
            result[tool.name] = git.newest(tool.source, tool.local)
        except git.GitError as error:
            result[tool.name] = error
    return result


def unreadable(error: git.GitError) -> str:
    """Zeile für ein Werkzeug ohne lesbaren neuesten Tag."""
    return _("newest tag not readable: {error}").format(error=error)


def target(tool: AnyPin, tag: str | git.GitError) -> AnyPin | None:
    """Das Werkzeug mit dem neuesten Tag; None, wenn eine Git-Quelle keinen lesbaren Tag hat.

    Eine Arbeitskopie als Quelle braucht zum Installieren keinen Tag; ohne lesbaren Tag bleibt
    sie bei dem der Config.
    """
    if isinstance(tag, str):
        return upgraded(tool, tag)
    return tool if tool.local else None


def pinned(pin: Pin, wanted: Pin) -> str:
    """Zeile eines gepinnten Tags: aktuell oder der neueste dazu."""
    if wanted.tag == pin.tag:
        return _("pinned, current ({tag})").format(tag=pin.tag)
    return _("pinned {old}, newest {new}").format(old=pin.tag, new=wanted.tag)


def preview(entries: list[Pin], newest: dict[str, str | git.GitError]) -> int:
    """Tabelle installiert, Config und neueste Version samt nötigem Schritt; installiert nichts."""
    found, failed = pipx.installed(), False
    rows = [[_("Tool"), _("Installed"), _("Config"), _("Newest"), ""]]
    for entry in entries:
        tag = newest[entry.name]
        before = found.get(entry.package) if isinstance(entry, Tool) else None
        wanted = target(entry, tag)
        if wanted is None:
            state, failed = unreadable(tag), True
        elif isinstance(wanted, Tool):
            result = plan(wanted, before)
            hint = _("{state} → devtools upgrade").format(state=result.text)
            state = hint if result.needed else result.text
        else:
            state = pinned(entry, wanted)
            if wanted.tag != entry.tag:
                state = _("{state} → devtools upgrade --write").format(state=state)
        version = semver(tag) if isinstance(tag, str) else "?"
        installed = before.version if before else "–"
        rows.append([entry.label, installed, entry.minimum or "?", version, state])
    widths = [max(len(row[column]) for row in rows) for column in range(4)]
    for row in rows:
        cells = [cell.ljust(width) for cell, width in zip(row, widths, strict=False)]
        print(f"  {'  '.join([*cells, row[4]]).rstrip()}")
    return 1 if failed else 0


def upgrade(entries: list[Pin], config: Path, write: bool, unsourced: list[str]) -> int:
    """Bringt jedes Werkzeug auf den neuesten Release-Tag seiner Quelle; mit write auch die Config.

    Ohne lesbaren Tag einer Git-Quelle meldet die Zeile den Grund, die übrigen Werkzeuge laufen
    weiter. Ein gepinnter Tag wird nur gemeldet und mit write geschrieben. Von einem Werkzeug kommt
    nur ein Tag in die Config, den die installierte Version danach erreicht; sonst scheiterte
    devtools check, und install könnte es nicht beheben.
    """
    found, newest, failed, handled = pipx.installed(), newest_tags(entries), False, []
    for entry in ordered(entries):
        wanted = target(entry, newest[entry.name])
        if wanted is None:
            line(entries, entry, unreadable(newest[entry.name]))
            failed = True
        elif not isinstance(wanted, Tool):
            line(entries, entry, pinned(entry, wanted))
            handled.append((entry, wanted))
        elif bring(entries, wanted, found):
            handled.append((entry, wanted))
        else:
            failed = True
    raised = [(entry, wanted) for entry, wanted in handled if wanted.tag != entry.tag]
    after = pipx.installed() if raised else {}
    reached = [pair for pair in raised if reaches_tag(after, *pair)]
    if write and reached:
        write_tags(config, {key(entry): wanted.tag for entry, wanted in reached})
    if write:
        for entry, wanted in handled:
            print(f"  {config}: {written(entry, wanted, (entry, wanted) in reached, after)}")
    elif reached:
        text = _("{config} still names older tags: devtools upgrade --write")
        print(f"  {text.format(config=config)}")
    without_source(config, unsourced)
    return 1 if failed else 0


def without_source(config: Path, unsourced: list[str]) -> None:
    """Je NAME_TAG ohne NAME_SOURCE eine Zeile: Den neuesten Tag kann upgrade nicht kennen."""
    for name in unsourced:
        text = _("{key} has no {source}: its newest tag is unknown")
        source = f"{name.removesuffix('_TAG')}_SOURCE"
        print(f"  {config}: {text.format(key=name, source=source)}")


def reaches_tag(after: dict[str, Installed], entry: Pin, wanted: Pin) -> bool:
    """Darf der neue Tag in die Config? Ein gepinnter immer, der eines Werkzeugs nur, wenn die
    installierte Version ihn erreicht."""
    return not isinstance(wanted, Tool) or reaches(after.get(wanted.package), wanted)


def written(entry: Pin, wanted: Pin, reached: bool, after: dict[str, Installed]) -> str:
    """Was --write mit dem Eintrag NAME_TAG machte: alt → neu, aktuell oder warum er bleibt."""
    if wanted.tag == entry.tag:
        return _("{key} current ({tag})").format(key=key(entry), tag=entry.tag)
    if reached:
        return f"{key(entry)} {entry.tag} → {wanted.tag}"
    now = after.get(entry.package) if isinstance(entry, Tool) else None
    text = _("{key} stays at {old}: installed {version} does not reach {new}")
    values = {"key": key(entry), "old": entry.tag, "new": wanted.tag}
    return text.format(version=now.version if now else "–", **values)


def reaches(found: Installed | None, tool: Tool) -> bool:
    """Erreicht die installierte Version den Tag des Werkzeugs?"""
    return found is not None and satisfies(found, tool)


def key(tool: Pin) -> str:
    """Der Eintrag NAME_TAG des Werkzeugs in der Config."""
    return f"{tool.name.upper()}_TAG"


def check(tool: Tool) -> int:
    """Mindestversion aus dem Tag; sonst Meldung samt Installationsbefehl und Exit 1."""
    found = pipx.installed().get(tool.package)
    if reaches(found, tool):
        return 0
    if found is None:
        text = _("✗ {label} missing (requires {minimum} or later): {command}")
    else:
        text = _("✗ {label} {version} is too old (requires {minimum} or later): {command}")
    values = {"label": tool.label, "minimum": tool.minimum, "command": shlex.join(tool.command())}
    sys.stderr.write(f"  {text.format(version=found and found.version, **values)}\n")
    return 1


def named(tools: list[AnyPin], name: str) -> AnyPin:
    """Das Werkzeug zu NAME, dem Präfix der Einträge, gleich in welcher Schreibung."""
    found = {tool.name: tool for tool in tools}
    if name.lower() not in found:
        text = _("✗ Unknown tool {name}; known: {known}")
        raise UnknownTool(text.format(name=repr(name), known=", ".join(found)))
    return found[name.lower()]


def parser() -> argparse.ArgumentParser:
    """Argumente: status, install, upgrade, check NAME, command NAME, --config und --version."""
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
    upgrading = commands.add_parser(
        "upgrade", help=_("bring each tool to the newest release tag of its source")
    )
    upgrading.add_argument("name", nargs="?", metavar=_("NAME"), help=_("only this tool"))
    upgrading.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help=_("show installed, config and newest version, install nothing"),
    )
    upgrading.add_argument(
        "--write",
        action="store_true",
        help=_("also write the newer tags into the config"),
    )
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
        if arguments.command == "upgrade":
            pins, unsourced = load_pins(arguments.config)
            entries = [*tools, *pins]
            if arguments.name:
                entries, unsourced = [named(entries, arguments.name)], []
            if arguments.dry_run:
                failed = preview(entries, newest_tags(entries))
                without_source(arguments.config, unsourced)
                return failed
            return upgrade(entries, arguments.config, arguments.write, unsourced)
        tool = named(tools, arguments.name)
        if arguments.command == "command":
            print(shlex.join(tool.command()))
            return 0
        return check(tool)
    except UnknownTool as error:
        sys.stderr.write(f"  {error}\n")
        return 2
    except (ConfigError, pipx.PipxError) as error:
        sys.stderr.write(f"  ✗ {error}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
