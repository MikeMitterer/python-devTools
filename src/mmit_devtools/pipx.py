"""Zugriff auf pipx: installierte Pakete lesen und ein Werkzeug installieren."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from mmit_devtools.i18n import _
from mmit_devtools.versions import working_copy_version


class PipxError(Exception):
    """pipx fehlt oder liefert keinen lesbaren Stand."""


@dataclass(frozen=True)
class Installed:
    """Was pipx für ein Paket installiert hat."""

    spec: str
    editable: bool
    version: str

    @property
    def local(self) -> bool:
        """Ist eine Arbeitskopie installiert (ein Ordner statt einer URL oder eines Pakets)?

        pipx führt eine Arbeitskopie mit absolutem Pfad, ein Paket von PyPI unter seinem bloßen
        Namen; ein gleichnamiger Ordner im aktuellen Ordner ist deshalb keine Arbeitskopie.
        """
        path = Path(self.spec)
        return path.is_absolute() and path.is_dir()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    """pipx-Aufruf mit erfasster Ausgabe; ohne pipx im PATH ein PipxError."""
    try:
        return subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError:
        raise PipxError(_("pipx is missing from PATH (https://pipx.pypa.io)")) from None


def installed() -> dict[str, Installed]:
    """Stand aller pipx-Pakete aus pipx list --json, je Paketname."""
    result = run(["pipx", "list", "--json"])
    if result.returncode:
        raise PipxError(_("pipx list failed: {error}").format(error=result.stderr.strip()))
    try:
        venvs = json.loads(result.stdout).get("venvs", {})
        return {package: entry(venv) for package, venv in venvs.items()}
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        text = _("pipx list --json is not readable: {error}")
        raise PipxError(text.format(error=error)) from None


def entry(venv: dict) -> Installed:
    """Ein Eintrag aus pipx list --json; eine bearbeitbare Arbeitskopie zählt mit ihrer Version."""
    main = venv["metadata"]["main_package"]
    spec = str(main.get("package_or_url") or main.get("package") or "")
    pip_args = main.get("pip_args") or []
    editable = "--editable" in pip_args or "-e" in pip_args
    version = str(main.get("package_version") or "?")
    found = Installed(spec, editable, version)
    if found.local and editable:
        return Installed(spec, editable, working_copy_version(Path(spec)) or version)
    return found
