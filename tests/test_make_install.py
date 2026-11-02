"""make install: Wheel aus diesem Stand im Cache des Nutzers, mit pipx samt Extra theme installiert.

pipx ist ein Ersatz, der jeden Aufruf protokolliert; das pipx des Rechners bleibt unberührt. Dass
das echte pipx die Angabe `name[theme] @ file://…` samt Extra installiert, ist in T-9 von Hand mit
einem isolierten PIPX_HOME belegt; die Angabe prüft der Test am Wortlaut.
"""

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# pipx environment --value PIPX_BIN_DIR nennt den Ordner mit dem devtools-Ersatz; install
# protokolliert seine Argumente, je Argument eine Zeile.
FAKE_PIPX = """#!/bin/sh
if [ "$1" = environment ]; then echo "$FAKE_BIN"; exit 0; fi
printf '%s\\n' "$@" >> "$FAKE_CALLS"
"""
FAKE_DEVTOOLS = "#!/bin/sh\necho 'devtools 9.9.9'\n"


def make_install(
    tmp_path: Path, with_pipx: bool, env: dict[str, str] | None = None
) -> tuple[subprocess.CompletedProcess, list[str]]:
    """make install mit eigenem XDG_CACHE_HOME; PATH ohne das echte pipx."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    calls = tmp_path / "calls.log"
    calls.write_text("")
    if with_pipx:
        for name, script in (("pipx", FAKE_PIPX), ("devtools", FAKE_DEVTOOLS)):
            (bin_dir / name).write_text(script)
            (bin_dir / name).chmod(0o755)
    # Nur diese Befehle aus dem PATH des Rechners: Ihr Ordner (etwa Homebrew) enthielte sonst
    # auch das echte pipx.
    for name in ("make", "bash", "git"):
        if not (bin_dir / name).exists():
            (bin_dir / name).symlink_to(shutil.which(name))
    result = subprocess.run(
        ["make", "--no-print-directory", "install"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PATH": os.pathsep.join([str(bin_dir), "/usr/bin", "/bin"]),
            "XDG_CACHE_HOME": str(tmp_path / "cache"),
            "FAKE_BIN": str(bin_dir),
            "FAKE_CALLS": str(calls),
            "NO_COLOR": "1",
            **(env or {}),
        },
    )
    return result, calls.read_text().splitlines()


def test_install_puts_wheel_in_cache_and_installs_it_with_theme(tmp_path):
    """Das Wheel liegt im Cache (nicht im Checkout), pipx bekommt es samt Extra theme als
    PEP-508-Angabe; ein älteres DevTools-Wheel dort wird ersetzt, fremde Dateien bleiben."""
    cache = tmp_path / "cache" / "mmit-devtools"
    cache.mkdir(parents=True)
    (cache / "mmit_devtools-0.0.1-py3-none-any.whl").write_text("alt")
    (cache / "fremd.whl").write_text("bleibt")
    result, calls = make_install(tmp_path, with_pipx=True)
    assert result.returncode == 0, result.stdout + result.stderr
    wheels = sorted(path.name for path in cache.glob("mmit_devtools-*.whl"))
    assert len(wheels) == 1 and wheels[0] != "mmit_devtools-0.0.1-py3-none-any.whl", wheels
    assert (cache / "fremd.whl").read_text() == "bleibt"
    spec = f"mmit-devtools[theme] @ file://{cache / wheels[0]}"
    assert calls == ["install", "--force", "--quiet", spec], calls
    assert "devtools 9.9.9 installiert" in result.stdout, result.stdout


def test_install_leaves_a_wheel_dir_of_the_caller_alone(tmp_path):
    """R1-F2: Eine Variable WHEEL_DIR aus der Shell des Aufrufers löscht nichts."""
    own = tmp_path / "wheelhouse"
    own.mkdir()
    (own / "eigenes.whl").write_text("bleibt")
    result, _ = make_install(tmp_path, with_pipx=True, env={"WHEEL_DIR": str(own)})
    assert result.returncode == 0, result.stdout + result.stderr
    assert (own / "eigenes.whl").read_text() == "bleibt"


def test_install_without_pipx_names_how_to_get_it(tmp_path):
    """Ohne pipx: Meldung mit Installationsweg, Exit ungleich 0, kein Wheel."""
    result, _ = make_install(tmp_path, with_pipx=False)
    assert result.returncode != 0
    assert "pipx fehlt" in result.stderr and "brew install pipx" in result.stderr, result.stderr
    assert not (tmp_path / "cache").exists()
