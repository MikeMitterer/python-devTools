"""devtools status, install, check und command gegen den pipx-Ersatz aus conftest."""

from conftest import GIT_BASHLIB, GIT_TOOLS, venv

BASHLIB_GIT_CALL = ["install", "--force", f"{GIT_BASHLIB}@v0.2.0+261031.2038.b22f0"]


def test_install_updates_outdated_tool_with_tag_and_leaves_current_one(sandbox):
    """Veraltet → pipx mit dem Tag, „updated“; aktuell → kein Aufruf."""
    result, calls = sandbox.run("install")
    assert result.returncode == 0, result.stderr
    assert calls == [BASHLIB_GIT_CALL], calls
    assert "ProjectTools  current (0.3.2)" in result.stdout, result.stdout
    assert "BashLib       updated from 0.1.0 to 0.2.0" in result.stdout, result.stdout


def test_install_reports_missing_tool_as_installed(sandbox):
    """Fehlt ein Werkzeug, installiert pipx es aus Quelle und Tag."""
    del sandbox.state["mmit-bashlib"]
    result, calls = sandbox.run("install")
    assert calls == [BASHLIB_GIT_CALL], calls
    assert f"BashLib       installed 0.2.0 ({GIT_BASHLIB})" in result.stdout, result.stdout


def test_working_copy_stays_untouched_when_config_wants_git(sandbox):
    """Eine bearbeitbare Arbeitskopie bleibt bei Git-Quelle unberührt; ihre Version zählt."""
    local = sandbox.working_copy("mmit-bashlib", "0.2.0")
    # pipx friert bei -e die Version beim Installieren ein (hier 0.1.0).
    sandbox.state["mmit-bashlib"] = venv(str(local), "0.1.0", editable=True)
    result, calls = sandbox.run("install")
    assert calls == [], calls
    assert f"working copy {local} (0.2.0), left untouched" in result.stdout, result.stdout
    checked, _ = sandbox.run("check", "bashlib")
    assert checked.returncode == 0, checked.stderr


def test_working_copy_as_source_installs_path_with_e(sandbox):
    """Eine Arbeitskopie als Quelle bekommt pipx als Pfad, mit -e nach EDITABLE."""
    local = sandbox.working_copy("mmit-bashlib", "0.2.0")
    sandbox.config["BASHLIB_SOURCE"] = "mmit-bashlib"
    result, calls = sandbox.run("install")
    assert calls == [["install", "--force", "-e", str(local.resolve())]], calls
    assert "updated from 0.1.0 to 0.2.0" in result.stdout, result.stdout

    again, calls = sandbox.run("install")
    assert calls == [], calls
    assert "BashLib       current (0.2.0, working copy" in again.stdout, again.stdout


def test_working_copy_without_editable_installs_path_without_e(sandbox):
    """EDITABLE=no: pipx bekommt den Pfad ohne -e."""
    local = sandbox.working_copy("mmit-bashlib", "0.2.0")
    sandbox.config["BASHLIB_SOURCE"] = str(local)
    sandbox.config["BASHLIB_EDITABLE"] = "no"
    _, calls = sandbox.run("install")
    assert calls == [["install", "--force", str(local.resolve())]], calls


def test_status_shows_without_installing(sandbox):
    """status ruft pipx nur zum Lesen auf und nennt den nötigen Schritt."""
    result, calls = sandbox.run("status")
    assert result.returncode == 0, result.stderr
    assert calls == [], calls
    assert "BashLib       0.1.0, wanted 0.2.0 → devtools install" in result.stdout


def test_check_fails_on_old_or_missing_tool_and_names_command(sandbox):
    """check: zu alt oder fehlend → Exit 1 mit Installationsbefehl; aktuell → Exit 0."""
    old, _ = sandbox.run("check", "bashlib")
    assert old.returncode == 1
    assert "BashLib 0.1.0 is too old (requires 0.2.0 or later)" in old.stderr, old.stderr
    assert f"pipx install --force {GIT_BASHLIB}@v0.2.0+261031.2038.b22f0" in old.stderr

    del sandbox.state["mmit-bashlib"]
    missing, _ = sandbox.run("check", "BASHLIB")
    assert missing.returncode == 1 and "BashLib missing" in missing.stderr, missing.stderr

    current, _ = sandbox.run("check", "projecttools")
    assert current.returncode == 0, current.stderr


def test_command_prints_install_command_quoted(sandbox):
    """command NAME gibt den pipx-Aufruf zum Kopieren aus, ein Pfad mit Leerzeichen gequotet."""
    result, _ = sandbox.run("command", "projecttools")
    assert result.stdout == f"pipx install --force {GIT_TOOLS}@v0.3.2+261029.1600.c7bbd\n"

    local = sandbox.working_copy("it's here", "0.2.0")
    sandbox.config["BASHLIB_SOURCE"] = str(local)
    quoted, _ = sandbox.run("command", "bashlib")
    assert quoted.stdout == f"pipx install --force -e '{sandbox.root}/it'\"'\"'s here'\n"


def test_tools_come_from_config(sandbox):
    """Welche Werkzeuge es gibt, steht in der Config: ein weiteres NAME_PACKAGE genügt."""
    local = sandbox.working_copy("mmit-cli-theme", "0.2.0")
    sandbox.config.update(
        CLI_THEME_PACKAGE="mmit-cli-theme", CLI_THEME_TAG="v0.2.0", CLI_THEME_SOURCE=str(local)
    )
    result, calls = sandbox.run("status")
    assert "mmit-cli-theme  missing → devtools install" in result.stdout, result.stdout
    checked, _ = sandbox.run("check", "cli_theme")
    assert checked.returncode == 1 and "mmit-cli-theme missing" in checked.stderr


def test_config_errors_name_file_and_key(sandbox):
    """Fehlende Config, fehlender Schlüssel oder unbekanntes Werkzeug enden mit Meldung."""
    source = sandbox.config.pop("BASHLIB_SOURCE")
    result, _ = sandbox.run("status")
    assert result.returncode == 1 and "BASHLIB_SOURCE is missing" in result.stderr, result.stderr
    sandbox.config["BASHLIB_SOURCE"] = source

    missing, _ = sandbox.run("--config", "nirgends.conf.sh", "status")
    assert missing.returncode == 1 and "nirgends.conf.sh is missing" in missing.stderr
    assert "PROJECTTOOLS_PACKAGE=mmit-projecttools" in missing.stderr

    unknown, _ = sandbox.run("check", "gibtsnicht")
    assert unknown.returncode == 2 and "known: projecttools" in unknown.stderr


def test_install_reports_pipx_failure(sandbox):
    """Scheitert pipx, nennt die Zeile den Befehl und install endet mit Exit 1."""
    result, _ = sandbox.run("install", env={"PIPX_FAIL": "1"})
    assert result.returncode == 1
    assert "BashLib       pipx failed" in result.stdout, result.stdout
    assert "gewollter Fehler" in result.stderr


def test_without_pipx_status_ends_with_hint(sandbox):
    """Ohne pipx im PATH: Meldung statt Traceback, Exit 1."""
    result, _ = sandbox.run("status", env={"PATH": "/usr/bin:/bin"})
    assert result.returncode == 1 and "pipx is missing" in result.stderr, result.stderr


def test_without_command_shows_help(sandbox):
    """Ohne Befehl zeigt devtools die Hilfe und legt nicht los."""
    result, calls = sandbox.run()
    assert result.returncode == 0 and "status" in result.stdout and calls == []


def test_output_follows_language(sandbox):
    """Mit LANGUAGE=de kommen Zeilen, Fehler und Hilfe aus dem deutschen Katalog."""
    result, _ = sandbox.run("install", env={"LANGUAGE": "de"})
    assert "ProjectTools  aktuell (0.3.2)" in result.stdout, result.stdout
    assert "BashLib       aktualisiert von 0.1.0 auf 0.2.0" in result.stdout, result.stdout

    del sandbox.state["mmit-bashlib"]
    missing, _ = sandbox.run("check", "bashlib", env={"LANGUAGE": "de"})
    assert "BashLib fehlt (verlangt ab 0.2.0)" in missing.stderr, missing.stderr

    shown, _ = sandbox.run("--help", env={"LANGUAGE": "de"})
    assert "--config DATEI" in shown.stdout and "Installationsbefehl" in shown.stdout
