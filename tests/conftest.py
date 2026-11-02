"""Gemeinsame Hilfen: pipx- und git-Ersatz im PATH und Aufruf des echten Befehls devtools.

Der pipx-Ersatz führt seinen Stand in einer Datei und protokolliert jeden Aufruf; der git-Ersatz
liefert die Tags je Quelle aus GIT_TAGS. Der echte Rechner, sein pipx und das Netz bleiben
unberührt.
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
# git ls-remote URL und git -C PFAD tag --list: die Tags aus GIT_TAGS je URL bzw. Pfad; eine
# unbekannte Quelle scheitert wie ein nicht erreichbares Remote.
FAKE_GIT = """\
import json, os, sys
args = sys.argv[1:]
where = args[1] if args[0] == "-C" else args[-1]
tags = json.loads(os.environ["GIT_TAGS"]).get(where)
if tags is None:
    sys.stderr.write(f"fatal: repository '{where}' not found\\n")
    sys.exit(128)
for tag in tags:
    print(f"0123abcd\\trefs/tags/{tag}" if "ls-remote" in args else tag)
"""
LAUNCHER = '#!/bin/sh\nexec "$FAKE_PYTHON" "$0.py" "$@"\n'


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
    tags: dict[str, list[str]]
    head: str = ""

    def working_copy(self, name: str, version: str) -> Path:
        """Arbeitskopie mit pyproject.toml in der genannten Version."""
        folder = self.root / name
        folder.mkdir(exist_ok=True)
        (folder / "pyproject.toml").write_text(
            f'[project]\nname = "{name}"\nversion = "{version}"\n'
        )
        return folder

    @property
    def conf(self) -> Path:
        """Die Config, die run schreibt und devtools liest."""
        return self.root / ".dev-tools.conf.sh"

    def conf_text(self) -> str:
        """Inhalt der Config: Kopf, dann je Eintrag NAME=wert."""
        return self.head + "".join(f"{key}={value}\n" for key, value in self.config.items())

    def run(self, *args: str, env: dict[str, str] | None = None):
        """devtools mit dieser Config und dem pipx-Ersatz; liefert Ergebnis und pipx-Aufrufe."""
        (self.root / "state.json").write_text(json.dumps(self.state))
        calls = self.root / "calls.log"
        calls.write_text("")
        self.conf.write_text(self.conf_text())
        environment = {
            "PATH": f"{self.root / 'bin'}:/usr/bin:/bin",
            # Nie die .mo aus dem Quellbaum: ein leerer Katalogordner, also Englisch.
            "DEVTOOLS_LOCALE_DIR": str(self.root / "locale"),
            "FAKE_PYTHON": sys.executable,
            "PIPX_STATE": str(self.root / "state.json"),
            "PIPX_CALLS": str(calls),
            "PIPX_GIT_PACKAGES": json.dumps(
                {GIT_TOOLS: "mmit-projecttools", GIT_BASHLIB: "mmit-bashlib"}
            ),
            "GIT_TAGS": json.dumps(self.tags),
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
    """ProjectTools aktuell, BashLib veraltet; beide mit Git-Quelle, deren neuester Tag dem der
    Config entspricht."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, script in (("pipx", FAKE_PIPX), ("git", FAKE_GIT)):
        (bin_dir / f"{name}.py").write_text(script)
        launcher = bin_dir / name
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
    tags = {
        GIT_TOOLS.removeprefix("git+"): ["v0.3.2+261029.1600.c7bbd"],
        GIT_BASHLIB.removeprefix("git+"): ["v0.1.0", "v0.2.0+261031.2038.b22f0"],
    }
    return Sandbox(tmp_path, state, config, tags)
