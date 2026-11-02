"""make install: Wheel aus diesem Stand, mit pipx samt Extra theme installiert; pipx ist ein Ersatz.

Der Ersatz protokolliert jeden Aufruf; das pipx des Rechners bleibt unberührt. Das Wheel entsteht
in einem temporären Ordner (WHEEL_DIR), nicht im build/ des Checkouts.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# pipx environment --value PIPX_BIN_DIR nennt den Ordner mit dem devtools-Ersatz; install
# protokolliert seine Argumente.
FAKE_PIPX = """#!/bin/sh
if [ "$1" = environment ]; then echo "$FAKE_BIN"; exit 0; fi
printf '%s\\n' "$*" >> "$FAKE_CALLS"
"""
FAKE_DEVTOOLS = "#!/bin/sh\necho 'devtools 9.9.9'\n"


def make_install(tmp_path: Path, with_pipx: bool) -> tuple[subprocess.CompletedProcess, list]:
    """make install mit eigenem WHEEL_DIR; PATH ohne das echte pipx."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls.log"
    calls.write_text("")
    if with_pipx:
        for name, script in (("pipx", FAKE_PIPX), ("devtools", FAKE_DEVTOOLS)):
            (bin_dir / name).write_text(script)
            (bin_dir / name).chmod(0o755)
    # Nur diese Befehle aus dem PATH des Rechners: Ihr Ordner (etwa Homebrew) enthielte sonst
    # auch das echte pipx.
    for name in ("make", "bash", "git"):
        (bin_dir / name).symlink_to(shutil.which(name))
    path = os.pathsep.join([str(bin_dir), "/usr/bin", "/bin"])
    result = subprocess.run(
        ["make", "--no-print-directory", "install", f"WHEEL_DIR={tmp_path / 'wheel'}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PATH": path,
            "FAKE_BIN": str(bin_dir),
            "FAKE_CALLS": str(calls),
            "NO_COLOR": "1",
        },
    )
    return result, calls.read_text().splitlines()


def test_install_builds_wheel_and_installs_it_with_theme(tmp_path):
    """Ein Wheel aus diesem Stand, pipx install --force mit Extra theme, danach die Version."""
    result, calls = make_install(tmp_path, with_pipx=True)
    assert result.returncode == 0, result.stdout + result.stderr
    wheels = list((tmp_path / "wheel").glob("mmit_devtools-*.whl"))
    assert len(wheels) == 1, wheels
    assert calls == [f"install --force --quiet {wheels[0]}[theme]"], json.dumps(calls)
    assert "devtools 9.9.9 installiert" in result.stdout, result.stdout


def test_install_without_pipx_names_how_to_get_it(tmp_path):
    """Ohne pipx: Meldung mit Installationsweg, Exit ungleich 0, kein Wheel."""
    result, calls = make_install(tmp_path, with_pipx=False)
    assert result.returncode != 0
    assert "pipx fehlt" in result.stderr and "brew install pipx" in result.stderr, result.stderr
    assert not (tmp_path / "wheel").exists()
