"""Abgleich zwischen Config und pipx: was ein Werkzeug braucht und was install daraus macht."""

from dataclasses import dataclass
from pathlib import Path

from mmit_devtools.config import Tool
from mmit_devtools.pipx import Installed
from mmit_devtools.versions import as_tuple, working_copy_version


@dataclass(frozen=True)
class Plan:
    """Zustand eines Werkzeugs als Text und ob install pipx aufrufen muss."""

    text: str
    needed: bool


def same_copy(tool: Tool, found: Installed) -> bool:
    """Ist genau die Arbeitskopie aus der Config installiert?"""
    return found.local and Path(found.spec).resolve() == Path(tool.source).resolve()


def satisfies(found: Installed, tool: Tool) -> bool:
    """Erfüllt die installierte Version die Mindestversion aus dem Tag?"""
    return as_tuple(found.version) >= as_tuple(tool.minimum)


def plan(tool: Tool, found: Installed | None) -> Plan:
    """Was zu tun ist, damit das Werkzeug Quelle und Tag der Config entspricht.

    Verlangt die Config Git, bleibt eine installierte Arbeitskopie unberührt: Wer lokal
    entwickelt, hat sie bewusst installiert.
    """
    if found is None:
        return Plan("fehlt", True)
    if tool.local:
        if not same_copy(tool, found) or found.editable != tool.editable:
            return Plan(f"{found.version} aus {found.spec}, verlangt {tool.source}", True)
        wanted = working_copy_version(Path(tool.source))
        if not tool.editable and as_tuple(found.version) < as_tuple(wanted):
            return Plan(f"{found.version}, Arbeitskopie hat {wanted}", True)
        return Plan(f"aktuell ({found.version}, Arbeitskopie {tool.source})", False)
    if found.local:
        return Plan(f"Arbeitskopie {found.spec} ({found.version}), unberührt", False)
    if not satisfies(found, tool):
        return Plan(f"{found.version}, verlangt {tool.minimum}", True)
    return Plan(f"aktuell ({found.version})", False)


def done(tool: Tool, before: Installed | None, after: Installed | None) -> str:
    """Meldung nach einem pipx-Aufruf: installiert oder aktualisiert von X auf Y."""
    new = after.version if after else "?"
    if before is None:
        return f"installiert {new} ({tool.source})"
    return f"aktualisiert von {before.version} auf {new} ({tool.source})"
