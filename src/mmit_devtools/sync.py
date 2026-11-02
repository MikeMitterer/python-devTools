"""Abgleich zwischen Config und pipx: was ein Werkzeug braucht und was install daraus macht."""

from dataclasses import dataclass, replace
from pathlib import Path

from mmit_devtools.config import Tool
from mmit_devtools.i18n import _
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


def upgraded(tool: Tool, newest: str) -> Tool:
    """Das Werkzeug mit dem neuesten Tag, wenn er über dem Tag der Config liegt."""
    if as_tuple(newest) > as_tuple(tool.minimum):
        return replace(tool, tag=newest)
    return tool


def plan(tool: Tool, found: Installed | None) -> Plan:
    """Was zu tun ist, damit das Werkzeug Quelle und Tag der Config entspricht.

    Verlangt die Config Git, bleibt eine installierte Arbeitskopie unberührt: Wer lokal
    entwickelt, hat sie bewusst installiert.
    """
    if found is None:
        return Plan(_("missing"), True)
    if tool.local:
        if not same_copy(tool, found) or found.editable != tool.editable:
            text = _("{version} from {source}, wanted {wanted}")
            return Plan(
                text.format(version=found.version, source=found.spec, wanted=tool.source), True
            )
        wanted = working_copy_version(Path(tool.source))
        if not tool.editable and as_tuple(found.version) < as_tuple(wanted):
            text = _("{version}, working copy has {wanted}")
            return Plan(text.format(version=found.version, wanted=wanted), True)
        text = _("current ({version}, working copy {path})")
        return Plan(text.format(version=found.version, path=tool.source), False)
    if found.local:
        text = _("working copy {path} ({version}), left untouched")
        return Plan(text.format(path=found.spec, version=found.version), False)
    if not satisfies(found, tool):
        text = _("{version}, wanted {wanted}")
        return Plan(text.format(version=found.version, wanted=tool.minimum), True)
    return Plan(_("current ({version})").format(version=found.version), False)


def done(tool: Tool, before: Installed | None, after: Installed | None) -> str:
    """Meldung nach einem pipx-Aufruf: installiert oder aktualisiert von X auf Y."""
    new = after.version if after else "?"
    if before is None:
        return _("installed {version} ({source})").format(version=new, source=tool.source)
    text = _("updated from {old} to {new} ({source})")
    return text.format(old=before.version, new=new, source=tool.source)
