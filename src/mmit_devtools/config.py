"""Config .dev-tools.conf.sh lesen: je Werkzeug pipx-Paket, Tag, Quelle und Einbindung.

Die Datei ist zugleich Make- und Bash-Syntax: NAME=wert ohne Anführungszeichen und ohne
Leerzeichen um das =. Ein # beginnt wie in Make überall einen Kommentar. Jedes NAME_PACKAGE
macht NAME zu einem Werkzeug; die Reihenfolge der Datei gilt.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path

from mmit_devtools.i18n import _
from mmit_devtools.versions import semver

CONFIG_NAME = ".dev-tools.conf.sh"
ENTRY = re.compile(r"^([A-Z][A-Z0-9_]*)=(.*)$")
# Einrückung, Name und Wert bis Leerraum oder Kommentar; der Rest der Zeile bleibt beim Schreiben.
VALUE = re.compile(r"^(\s*)([A-Z][A-Z0-9_]*)=([^\s#]*)")
GIT_PREFIXES = ("git+", "http://", "https://")
YES, NO = ("yes", "true", "1"), ("no", "false", "0")

EXAMPLE = """\
PROJECTTOOLS_PACKAGE=mmit-projecttools
PROJECTTOOLS_LABEL=ProjectTools
PROJECTTOOLS_TAG=v0.3.2+261029.1600.c7bbd
PROJECTTOOLS_SOURCE=git+https://github.com/MikeMitterer/bash-ProjectTools.git
PROJECTTOOLS_EDITABLE=yes
"""


class ConfigError(Exception):
    """Config fehlt oder ist unvollständig; der Text nennt Datei und Schlüssel."""


def is_git(source: str) -> bool:
    """Ist die Quelle eine Git-URL statt eines Pfads?"""
    return source.startswith(GIT_PREFIXES)


@dataclass(frozen=True)
class Tool:
    """Was die Config für ein Werkzeug verlangt."""

    name: str
    package: str
    label: str
    tag: str
    source: str
    editable: bool

    @property
    def local(self) -> bool:
        """Ist die Quelle eine Arbeitskopie?"""
        return not is_git(self.source)

    @property
    def minimum(self) -> str | None:
        """Mindestversion: der SemVer-Teil des Tags."""
        return semver(self.tag)

    def command(self) -> list[str]:
        """pipx-Aufruf, der das Werkzeug auf Quelle und Tag bringt."""
        if self.local:
            return ["pipx", "install", "--force", *(["-e"] if self.editable else []), self.source]
        return ["pipx", "install", "--force", f"{self.source}@{self.tag}"]


def read_entries(path: Path) -> dict[str, str]:
    """NAME=wert-Zeilen in Dateireihenfolge; Kommentare und andere Zeilen zählen nicht."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ConfigError(
            _("{path} is missing. Example:").format(path=path) + f"\n\n{EXAMPLE}"
        ) from None
    except OSError as error:
        raise ConfigError(f"{path}: {error.strerror}") from None
    entries = {}
    for raw in text.splitlines():
        match = ENTRY.match(raw.split("#", 1)[0].strip())
        if match:
            entries[match.group(1)] = match.group(2).strip()
    return entries


def write_tags(path: Path, tags: dict[str, str]) -> None:
    """Ersetzt den Wert der genannten NAME_TAG-Einträge; alle übrigen Zeichen bleiben.

    newline="": Zeilenenden wie \\r\\n bleiben, wie sie sind.
    """
    with path.open(encoding="utf-8", newline="") as stream:
        lines = stream.readlines()
    for index, raw in enumerate(lines):
        match = VALUE.match(raw)
        if match and match.group(2) in tags:
            lines[index] = f"{match.group(1)}{match.group(2)}={tags[match.group(2)]}"
            lines[index] += raw[match.end() :]
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.writelines(lines)


def load_tools(path: Path) -> list[Tool]:
    """Alle Werkzeuge der Config; ein fehlender Pflichtwert ist ein Fehler mit seinem Schlüssel."""
    entries = read_entries(path)
    prefixes = [key.removesuffix("_PACKAGE") for key in entries if key.endswith("_PACKAGE")]
    if not prefixes:
        text = _("{path}: no tool (NAME_PACKAGE). Example:").format(path=path)
        raise ConfigError(f"{text}\n\n{EXAMPLE}")
    return [tool(path, entries, prefix) for prefix in prefixes]


def tool(path: Path, entries: dict[str, str], prefix: str) -> Tool:
    """Ein Werkzeug aus den Einträgen NAME_*; ein relativer Pfad gilt ab dem Ordner der Config."""

    def required(key: str) -> str:
        value = entries.get(f"{prefix}_{key}", "")
        if not value:
            raise ConfigError(
                _("{path}: {key} is missing").format(path=path, key=f"{prefix}_{key}")
            )
        return value

    package, tag, source = required("PACKAGE"), required("TAG"), required("SOURCE")
    if not is_git(source):
        source = str((path.parent / os.path.expanduser(source)).resolve())
    editable = entries.get(f"{prefix}_EDITABLE", "yes").lower()
    if editable not in YES + NO:
        text = _("{path}: {key} is {value}, allowed are yes and no")
        raise ConfigError(text.format(path=path, key=f"{prefix}_EDITABLE", value=repr(editable)))
    label = entries.get(f"{prefix}_LABEL") or package
    return Tool(prefix.lower(), package, label, tag, source, editable in YES)
