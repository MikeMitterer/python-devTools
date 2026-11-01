"""Gemeinsame Hilfen: pipx-Ersatz im PATH und Aufruf des echten Befehls devtools.

Der pipx-Ersatz führt seinen Stand in einer Datei und protokolliert jeden Aufruf; der echte
Rechner und sein pipx bleiben unberührt.
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

# Der installierte Befehl aus der venv der Tests, nicht ein Modulaufruf. Gestartet über Python:
# In einem Checkout-Pfad mit $(…) würde die sh-Zeile, die pip ins Skript schreibt, ihn auswerten.
COMMAND = Path(sys.executable).parent / "devtools"

GIT_BASHLIB = "git+https://github.com/MikeMitterer/bash-lib.git"
GIT_TOOLS = "git+https://github.com/MikeMitterer/bash-ProjectTools.git"

# list --json liefert den Stand aus PIPX_STATE, install schreibt ihn neu und protokolliert den
# Aufruf in PIPX_CALLS. Das Paket einer Git-URL steht in PIPX_GIT_PACKAGES, die Version im Tag.
# Gestartet über LAUNCHER: Ein Shebang mit dem Python-Pfad bräche an Leerzeichen im Checkout-Pfad.
FAKE_PIPX = """\
import json, os, re, sys, tomllib
from pathlib import Path
state = Path(os.environ["PIPX_STATE"])
data = json.loads(state.read_text())
if sys.argv[1:3] == ["list", "--json"]:
    print(json.dumps({"venvs": data}))
    sys.exit(0)
with open(os.environ["PIPX_CALLS"], "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")
if os.environ.get("PIPX_FAIL"):
    sys.stderr.write("pipx: gewollter Fehler\\n")
    sys.exit(1)
args = [a for a in sys.argv[2:] if a != "--force"]
editable = "-e" in args
spec = [a for a in args if a != "-e"][0]
if spec.startswith("git+"):
    url, tag = spec.rsplit("@", 1)
    package = json.loads(os.environ["PIPX_GIT_PACKAGES"])[url]
    version = re.search(r"(\\d+\\.\\d+\\.\\d+)", tag).group(1)
else:
    project = tomllib.loads((Path(spec) / "pyproject.toml").read_text())["project"]
    package, version = project["name"], project["version"]
data[package] = {"metadata": {"main_package": {
    "package": package, "package_or_url": spec, "package_version": version,
    "pip_args": ["--editable"] if editable else []}}}
state.write_text(json.dumps(data))
"""
LAUNCHER = '#!/bin/sh\nexec "$PIPX_PYTHON" "$PIPX_SCRIPT" "$@"\n'


def venv(spec: str, version: str, editable: bool = False) -> dict:
    """pipx-Eintrag wie in pipx list --json."""
    return {
        "metadata": {
            "main_package": {
                "package_or_url": spec,
                "package_version": version,
                "pip_args": ["--editable"] if editable else [],
            }
        }
    }


@dataclass
class Sandbox:
    """Temporärer Ordner mit pipx-Ersatz, Config und pipx-Stand; run startet devtools darin."""

    root: Path
    state: dict
    config: dict[str, str]

    def working_copy(self, name: str, version: str) -> Path:
        """Arbeitskopie mit pyproject.toml in der genannten Version."""
        folder = self.root / name
        folder.mkdir(exist_ok=True)
        (folder / "pyproject.toml").write_text(
            f'[project]\nname = "{name}"\nversion = "{version}"\n'
        )
        return folder

    def run(self, *args: str, env: dict[str, str] | None = None):
        """devtools mit dieser Config und dem pipx-Ersatz; liefert Ergebnis und pipx-Aufrufe."""
        (self.root / "state.json").write_text(json.dumps(self.state))
        calls = self.root / "calls.log"
        calls.write_text("")
        conf = self.root / ".dev-tools.conf.sh"
        conf.write_text("".join(f"{key}={value}\n" for key, value in self.config.items()))
        environment = {
            "PATH": f"{self.root / 'bin'}:/usr/bin:/bin",
            "PIPX_PYTHON": sys.executable,
            "PIPX_SCRIPT": str(self.root / "bin" / "fake_pipx.py"),
            "PIPX_STATE": str(self.root / "state.json"),
            "PIPX_CALLS": str(calls),
            "PIPX_GIT_PACKAGES": json.dumps(
                {GIT_TOOLS: "mmit-projecttools", GIT_BASHLIB: "mmit-bashlib"}
            ),
            **(env or {}),
        }
        result = subprocess.run(
            [sys.executable, str(COMMAND), *args],
            capture_output=True,
            text=True,
            env=environment,
            cwd=self.root,
        )
        self.state = json.loads((self.root / "state.json").read_text())
        return result, [json.loads(call) for call in calls.read_text().splitlines()]


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    """ProjectTools aktuell, BashLib veraltet; beide mit Git-Quelle."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "fake_pipx.py").write_text(FAKE_PIPX)
    launcher = bin_dir / "pipx"
    launcher.write_text(LAUNCHER)
    launcher.chmod(0o755)
    config = {
        "PROJECTTOOLS_PACKAGE": "mmit-projecttools",
        "PROJECTTOOLS_LABEL": "ProjectTools",
        "PROJECTTOOLS_TAG": "v0.3.2+261029.1600.c7bbd",
        "PROJECTTOOLS_SOURCE": GIT_TOOLS,
        "BASHLIB_PACKAGE": "mmit-bashlib",
        "BASHLIB_LABEL": "BashLib",
        "BASHLIB_TAG": "v0.2.0+261031.2038.b22f0",
        "BASHLIB_SOURCE": GIT_BASHLIB,
    }
    state = {
        "mmit-projecttools": venv(f"{GIT_TOOLS}@v0.3.2+261029.1600.c7bbd", "0.3.2"),
        "mmit-bashlib": venv(f"{GIT_BASHLIB}@v0.1.0", "0.1.0"),
    }
    return Sandbox(tmp_path, state, config)
