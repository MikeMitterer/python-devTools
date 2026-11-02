"""devtools upgrade: neuester Release-Tag je Werkzeug, Vorschau mit -n, Config mit --write."""

import json
import subprocess

from conftest import GIT_BASHLIB, GIT_TOOLS, venv

BASHLIB_REMOTE = GIT_BASHLIB.removeprefix("git+")
TOOLS_REMOTE = GIT_TOOLS.removeprefix("git+")
NEWEST = "v0.10.0+261102.0900.a1b2c"


def test_upgrade_installs_newest_release_tag_and_ignores_foreign_tags(sandbox):
    """Sortiert nach Version, nicht nach Text; fremde Tags und Vorabversionen zählen nicht."""
    sandbox.tags[BASHLIB_REMOTE] = [
        "v0.1.0",
        "v0.9.0+261101.1000.ffff0",
        NEWEST,
        "latest",
        "v1.0.0-rc1",
        "v2.0",
    ]
    result, calls = sandbox.run("upgrade")
    assert result.returncode == 0, result.stderr
    assert calls == [["install", "--force", f"{GIT_BASHLIB}@{NEWEST}"]], calls
    assert "ProjectTools  current (0.3.2)" in result.stdout, result.stdout
    assert "BashLib       updated from 0.1.0 to 0.10.0" in result.stdout, result.stdout
    # Ohne --write bleibt die Config, die Ausgabe nennt den Weg.
    assert f"BASHLIB_TAG={sandbox.config['BASHLIB_TAG']}" in sandbox.conf.read_text()
    assert "devtools upgrade --write" in result.stdout, result.stdout


def test_upgrade_name_limits_the_run_to_one_tool(sandbox):
    """upgrade NAME fasst nur dieses Werkzeug an."""
    sandbox.tags[TOOLS_REMOTE].append("v0.4.0+261102.0800.c0ffe")
    result, calls = sandbox.run("upgrade", "projecttools")
    assert calls == [["install", "--force", f"{GIT_TOOLS}@v0.4.0+261102.0800.c0ffe"]], calls
    assert "BashLib" not in result.stdout, result.stdout

    unknown, _ = sandbox.run("upgrade", "gibtsnicht")
    assert unknown.returncode == 2 and "known: projecttools" in unknown.stderr


def test_dry_run_shows_installed_config_and_newest_version_without_installing(sandbox):
    """-n und --dry-run: Tabelle, kein pipx-Aufruf, Config unverändert."""
    sandbox.tags[BASHLIB_REMOTE].append(NEWEST)
    for flag in ("-n", "--dry-run"):
        result, calls = sandbox.run("upgrade", flag, "--write")
        assert result.returncode == 0, result.stderr
        assert calls == [], calls
        rows = result.stdout.splitlines()
        assert rows[0].split() == ["Tool", "Installed", "Config", "Newest"], rows
        assert rows[1].split()[:4] == ["ProjectTools", "0.3.2", "0.3.2", "0.3.2"], rows
        assert rows[2].split()[:4] == ["BashLib", "0.1.0", "0.2.0", "0.10.0"], rows
        assert rows[2].endswith("→ devtools upgrade"), rows
        assert "BASHLIB_TAG=v0.2.0+261031.2038.b22f0" in sandbox.conf.read_text()


def test_write_replaces_older_tags_and_keeps_every_other_byte(sandbox):
    """--write ersetzt nur den Wert des veralteten NAME_TAG; Kommentare bleiben."""
    sandbox.head = "#!/usr/bin/env bash\n# Werkzeuge\n\n"
    sandbox.config["BASHLIB_TAG"] = "v0.2.0+261031.2038.b22f0  # BashLib"
    sandbox.tags[BASHLIB_REMOTE].append(NEWEST)
    before = sandbox.conf_text()
    result, _ = sandbox.run("upgrade", "--write")
    assert result.returncode == 0, result.stderr
    expected = before.replace("BASHLIB_TAG=v0.2.0+261031.2038.b22f0  #", f"BASHLIB_TAG={NEWEST}  #")
    assert sandbox.conf.read_text() == expected
    assert f"BASHLIB_TAG v0.2.0+261031.2038.b22f0 → {NEWEST}" in result.stdout, result.stdout


def test_unreachable_remote_or_missing_tag_is_reported_and_others_continue(sandbox):
    """Ein Werkzeug ohne lesbaren Tag: Meldung, die übrigen laufen weiter, Exit 1."""
    del sandbox.tags[TOOLS_REMOTE]
    result, calls = sandbox.run("upgrade")
    assert result.returncode == 1
    assert "ProjectTools  newest tag not readable: fatal: repository" in result.stdout
    assert calls == [["install", "--force", f"{GIT_BASHLIB}@v0.2.0+261031.2038.b22f0"]], calls

    sandbox.tags[TOOLS_REMOTE] = ["latest", "v1.0"]
    shown, _ = sandbox.run("upgrade", "-n")
    assert shown.returncode == 1
    assert "no release tag (vX.Y.Z)" in shown.stdout, shown.stdout


def test_working_copy_as_source_takes_newest_local_tag(sandbox):
    """Arbeitskopie als Quelle: neuester Tag des lokalen Repos für Anzeige und Config; eine
    bearbeitbare Arbeitskopie ist schon live eingebunden, pipx bleibt still."""
    local = sandbox.working_copy("mmit-bashlib", "0.3.0")
    sandbox.config["BASHLIB_SOURCE"] = "mmit-bashlib"
    sandbox.state["mmit-bashlib"] = venv(str(local.resolve()), "0.1.0", editable=True)
    sandbox.tags[str(local.resolve())] = ["v0.2.0+261031.2038.b22f0", "v0.3.0+261102.1000.0abc1"]
    shown, calls = sandbox.run("upgrade", "-n")
    assert calls == [], calls
    assert shown.stdout.splitlines()[2].split()[:4] == ["BashLib", "0.3.0", "0.2.0", "0.3.0"]

    result, calls = sandbox.run("upgrade", "--write")
    assert result.returncode == 0, result.stderr
    assert calls == [], calls
    assert "BASHLIB_TAG=v0.3.0+261102.1000.0abc1" in sandbox.conf.read_text()


def test_working_copy_installed_while_config_wants_git_stays(sandbox):
    """Wie bei install: eine selbst installierte Arbeitskopie bleibt unberührt."""
    local = sandbox.working_copy("mmit-bashlib", "0.2.0")
    sandbox.state["mmit-bashlib"] = venv(str(local), "0.2.0", editable=True)
    sandbox.tags[BASHLIB_REMOTE].append(NEWEST)
    result, calls = sandbox.run("upgrade")
    assert calls == [], calls
    assert "left untouched" in result.stdout, result.stdout


def test_devtools_itself_comes_last(sandbox):
    """Steht devtools selbst in der Config, ersetzt pipx die laufende venv; deshalb zuletzt."""
    remote = "git+https://example.invalid/python-devtools.git"
    config = {
        "DEVTOOLS_PACKAGE": "mmit-devtools",
        "DEVTOOLS_TAG": "v0.2.0+261101.1319.09840",
        "DEVTOOLS_SOURCE": remote,
    }
    sandbox.config = {**config, **sandbox.config}
    sandbox.tags[remote.removeprefix("git+")] = ["v0.3.0+261102.1100.d0d0d"]
    sandbox.tags[BASHLIB_REMOTE].append(NEWEST)
    packages = {
        GIT_TOOLS: "mmit-projecttools",
        GIT_BASHLIB: "mmit-bashlib",
        remote: "mmit-devtools",
    }
    for command in ("install", "upgrade"):
        result, calls = sandbox.run(command, env={"PIPX_GIT_PACKAGES": json.dumps(packages)})
        assert result.returncode == 0, result.stderr
        assert calls[-1][-1].startswith(f"{remote}@"), calls
        assert result.stdout.index("mmit-devtools") > result.stdout.index("BashLib"), result.stdout


def test_write_keeps_tag_that_the_installed_version_does_not_reach(sandbox):
    """R1-F1: --write schreibt nur Tags, die die installierte Version danach erreicht; sonst
    scheiterte check, und install könnte es nicht beheben."""
    local = sandbox.working_copy("mmit-bashlib", "0.2.0")
    sandbox.state["mmit-bashlib"] = venv(str(local), "0.2.0", editable=True)
    sandbox.tags[BASHLIB_REMOTE].append(NEWEST)
    result, calls = sandbox.run("upgrade", "--write")
    assert result.returncode == 0, result.stderr
    assert calls == [], calls
    assert "BASHLIB_TAG=v0.2.0+261031.2038.b22f0" in sandbox.conf.read_text()
    assert (
        f"BASHLIB_TAG stays at v0.2.0+261031.2038.b22f0: installed 0.2.0 does not reach {NEWEST}"
        in result.stdout
    ), result.stdout
    checked, _ = sandbox.run("check", "bashlib")
    assert checked.returncode == 0, checked.stderr


def test_write_keeps_local_tag_ahead_of_the_working_copy(sandbox):
    """R1-F1: Arbeitskopie als Quelle mit pyproject 0.3.0, das Repo hat schon v0.4.0."""
    local = sandbox.working_copy("mmit-bashlib", "0.3.0")
    sandbox.config["BASHLIB_SOURCE"] = "mmit-bashlib"
    sandbox.state["mmit-bashlib"] = venv(str(local.resolve()), "0.3.0", editable=True)
    sandbox.tags[str(local.resolve())] = ["v0.3.0+261102.1000.0abc1", "v0.4.0+261102.1200.0abc2"]
    result, _ = sandbox.run("upgrade", "--write")
    assert result.returncode == 0, result.stderr
    assert "BASHLIB_TAG=v0.2.0+261031.2038.b22f0" in sandbox.conf.read_text()
    checked, _ = sandbox.run("check", "bashlib")
    assert checked.returncode == 0, checked.stderr


def test_working_copy_without_readable_tag_is_no_failure(sandbox):
    """R1-F2: Eine Arbeitskopie als Quelle braucht keinen Tag zum Installieren; ohne lesbaren Tag
    meldet upgrade sie als Arbeitskopie und endet mit Exit 0."""
    local = sandbox.working_copy("mmit-bashlib", "0.2.0")
    sandbox.config["BASHLIB_SOURCE"] = "mmit-bashlib"
    sandbox.state["mmit-bashlib"] = venv(str(local.resolve()), "0.2.0", editable=True)
    result, calls = sandbox.run("upgrade", "--write")
    assert result.returncode == 0, result.stdout
    assert calls == [], calls
    assert "BashLib       current (0.2.0, working copy" in result.stdout, result.stdout
    shown, _ = sandbox.run("upgrade", "-n")
    assert shown.returncode == 0, shown.stdout
    assert shown.stdout.splitlines()[2].split()[:4] == ["BashLib", "0.2.0", "0.2.0", "?"]


DEVTOOLS_GIT = "git+https://example.invalid/python-devtools.git"
PINNED = "v0.2.0+261101.1319.09840"
PINNED_NEWEST = "v0.3.0+261102.1100.d0d0d"


def pin_devtools(sandbox):
    """DEVTOOLS_TAG mit Quelle, aber ohne Paket: gepinnt für pipx run wie in AgentLessons."""
    sandbox.config.update(DEVTOOLS_TAG=PINNED, DEVTOOLS_SOURCE=DEVTOOLS_GIT)
    sandbox.tags[DEVTOOLS_GIT.removeprefix("git+")] = [PINNED, PINNED_NEWEST]


def test_pinned_tag_without_package_is_updated_but_not_installed(sandbox):
    """NAME_TAG und NAME_SOURCE ohne NAME_PACKAGE: upgrade sucht den neuesten Tag, installiert
    nichts und schreibt ihn mit --write."""
    pin_devtools(sandbox)
    result, calls = sandbox.run("upgrade")
    assert result.returncode == 0, result.stderr
    assert all(DEVTOOLS_GIT not in " ".join(call) for call in calls), calls
    assert f"devtools      pinned {PINNED}, newest {PINNED_NEWEST}" in result.stdout, result.stdout
    assert "devtools upgrade --write" in result.stdout, result.stdout

    shown, _ = sandbox.run("upgrade", "-n", "devtools")
    rows = shown.stdout.splitlines()
    assert rows[1].split()[:4] == ["devtools", "–", "0.2.0", "0.3.0"], rows
    assert rows[1].endswith("→ devtools upgrade --write"), rows

    written, calls = sandbox.run("upgrade", "--write", "devtools")
    assert written.returncode == 0, written.stderr
    assert calls == [], calls
    assert f"DEVTOOLS_TAG={PINNED_NEWEST}" in sandbox.conf.read_text()
    assert f"DEVTOOLS_TAG {PINNED} → {PINNED_NEWEST}" in written.stdout, written.stdout


def test_tag_without_source_is_named(sandbox):
    """Altes Format nur mit NAME_TAG: upgrade kennt keine Quelle und sagt das, ohne zu scheitern."""
    sandbox.config["CLI_THEME_TAG"] = "v0.1.0"
    result, _ = sandbox.run("upgrade")
    assert result.returncode == 0, result.stderr
    assert "CLI_THEME_TAG has no CLI_THEME_SOURCE: its newest tag is unknown" in result.stdout
    shown, _ = sandbox.run("upgrade", "-n")
    assert "CLI_THEME_TAG has no CLI_THEME_SOURCE" in shown.stdout, shown.stdout


def test_write_names_every_tag_old_to_new_or_current(sandbox):
    """Mit --write nennt die Ausgabe je Eintrag alt → neu oder aktuell."""
    sandbox.tags[BASHLIB_REMOTE].append(NEWEST)
    pin_devtools(sandbox)
    result, _ = sandbox.run("upgrade", "--write")
    conf = ".dev-tools.conf.sh"
    assert f"{conf}: PROJECTTOOLS_TAG current (v0.3.2+261029.1600.c7bbd)" in result.stdout
    assert f"{conf}: BASHLIB_TAG v0.2.0+261031.2038.b22f0 → {NEWEST}" in result.stdout
    assert f"{conf}: DEVTOOLS_TAG {PINNED} → {PINNED_NEWEST}" in result.stdout, result.stdout


def test_written_config_stays_valid_for_bash_and_make(sandbox):
    """Die geschriebene Config bleibt für bash -n, source und Make-include gültig."""
    sandbox.head = "#!/usr/bin/env bash\n# Werkzeuge; Kommentar mit = und #\n\n"
    sandbox.config["BASHLIB_LABEL"] = "BashLib  # Name in der Ausgabe"
    sandbox.tags[BASHLIB_REMOTE].append(NEWEST)
    pin_devtools(sandbox)
    result, _ = sandbox.run("upgrade", "--write")
    assert result.returncode == 0, result.stderr
    conf = sandbox.conf
    assert subprocess.run(["bash", "-n", str(conf)]).returncode == 0
    sourced = subprocess.run(
        ["bash", "-c", 'source "$1"; printf "%s %s" "$BASHLIB_TAG" "$DEVTOOLS_TAG"', "-", conf],
        capture_output=True,
        text=True,
    )
    assert sourced.stdout == f"{NEWEST} {PINNED_NEWEST}", sourced.stderr
    makefile = sandbox.root / "Makefile"
    makefile.write_text(
        "include .dev-tools.conf.sh\nshow:\n\t@printf '%s %s' '$(BASHLIB_TAG)' '$(DEVTOOLS_TAG)'\n"
    )
    made = subprocess.run(["make", "-s", "show"], cwd=sandbox.root, capture_output=True, text=True)
    assert made.stdout == f"{NEWEST} {PINNED_NEWEST}", made.stderr
