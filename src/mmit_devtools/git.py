"""Zugriff auf git: neuester Release-Tag einer Git-Quelle oder einer Arbeitskopie."""

import os
import re
import shlex
import subprocess

from mmit_devtools.i18n import _
from mmit_devtools.versions import as_tuple

# vX.Y.Z, optional mit Build-Teil wie +261031.2038.b22f0; Vorabversionen wie -rc1 zählen nicht.
RELEASE = re.compile(r"^v\d+\.\d+\.\d+(\+[0-9A-Za-z.]+)?$")
TIMEOUT = 60


class GitError(Exception):
    """git fehlt, die Quelle ist nicht erreichbar oder hat keinen Release-Tag."""


def tags(source: str, local: bool) -> list[str]:
    """Alle Tags: git ls-remote bei einer Git-URL, git tag im Repo einer Arbeitskopie.

    GIT_TERMINAL_PROMPT=0: Ein Remote, das Zugangsdaten verlangt, scheitert, statt zu warten.
    """
    if local:
        command = ["git", "-C", source, "tag", "--list"]
    else:
        command = ["git", "ls-remote", "--tags", "--refs", source.removeprefix("git+")]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except FileNotFoundError:
        raise GitError(_("git is missing from PATH")) from None
    except subprocess.TimeoutExpired:
        raise GitError(_("git took longer than {seconds} s").format(seconds=TIMEOUT)) from None
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        text = _("{command} failed").format(command=shlex.join(command))
        raise GitError(lines[-1] if lines else text)
    if local:
        return result.stdout.split()
    return [
        line.split("\t", 1)[-1].removeprefix("refs/tags/") for line in result.stdout.splitlines()
    ]


def newest(source: str, local: bool) -> str:
    """Der neueste Release-Tag nach Version; bei gleicher Version entscheidet der Build-Teil."""
    found = [tag for tag in tags(source, local) if RELEASE.match(tag)]
    if not found:
        raise GitError(_("no release tag (vX.Y.Z) in {source}").format(source=source))
    return max(found, key=lambda tag: (as_tuple(tag), tag))
