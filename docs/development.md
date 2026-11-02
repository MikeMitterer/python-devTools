# Entwicklung

[← README](../README.de.md)

Diese Seite beschreibt die Arbeit **an** DevTools: Einrichten aus dem
Checkout, Tests, Aufbau und Release. Alle Befehle zeigt `make help`, die
Reihenfolge für den ersten Start `make hints`.

## Übersicht

- [Voraussetzungen](#voraussetzungen)
- [Einrichten](#einrichten)
- [Tests](#tests)
- [Übersetzungen](#übersetzungen)
- [Aufbau](#aufbau)
- [Version und Release](#version-und-release)

## Voraussetzungen

Python 3.14 oder neuer, wie `requires-python` in `pyproject.toml` verlangt;
`make setup` nimmt `python3.14`, ein anderer Interpreter geht mit
`PYTHON_BOOTSTRAP=…`. Zur Laufzeit braucht das Paket nur die
Standardbibliothek; das Extra `theme` bringt CLITheme (`mmit-cli-theme`, als
Git-Tag in `pyproject.toml`) und rich für farbige Ausgabe. `make setup`
installiert es über das Extra `dev` mit, damit die Tests beide Wege prüfen.
CLITheme führt `mmit-devtools` nie als Abhängigkeit, so entsteht kein Zirkel.

Die Prüfungen brauchen ProjectTools (`docs-check`, `repo-status`,
`changelog`), Releases zusätzlich BashLib, beide über pipx. Paket, Tag und
Quelle stehen in `.dev-tools.conf.sh`. Geprüft und gezeigt werden sie mit
`devtools` aus der `.venv`, also erst nach `make setup`: `make setup` und
`make info` zeigen den Stand, `make hints` die Installationsbefehle, und

```bash
make install-tools
```

bringt beide auf Quelle und Tag; eine selbst installierte Arbeitskopie bleibt
dabei unberührt.

[↑ Übersicht](#übersicht)

## Einrichten

```bash
make setup
```

`setup` legt die `.venv` an, installiert das Paket editierbar samt pytest,
Ruff und Babel (Extra `dev` in `pyproject.toml`), übersetzt die Kataloge nach
`.mo` und aktiviert den pre-commit-Hook unter `.githooks/`, der vor jedem
Commit die Doku prüft. Ein zweiter Aufruf ist
schnell; neu installiert wird nur, wenn `pyproject.toml` sich geändert hat.
Danach steht `.venv/bin/devtools` bereit.

```bash
make install
```

`install` bringt DevTools selbst aus diesem Stand auf den Rechner, mit den
Farben von CLITheme (`scripts/install-devtools.sh`). Es baut ein Wheel in einem
temporären Ordner, legt es unter `${XDG_CACHE_HOME:-~/.cache}/mmit-devtools/`
ab, ersetzt dort ein älteres DevTools-Wheel und installiert es mit
`pipx install --force "mmit-devtools[theme] @ file://<wheel>"`. Nur in dieser
Form installiert pipx das Extra mit; `<wheel>[theme]` übergeht es. Das Wheel
liegt im Cache statt im Checkout, weil pipx sich die Datei als Quelle merkt:
`pipx reinstall` klappt so auch, nachdem ein Worktree aufgeräumt ist. Aus
demselben Grund kein `pipx install -e`. Wer an DevTools
arbeitet und Änderungen sofort im Befehl sehen will, nimmt
`pipx install -e` (siehe `make hints`). `make install-tools` ist etwas
anderes: Es installiert die Werkzeuge aus `.dev-tools.conf.sh`, nicht DevTools.

[↑ Übersicht](#übersicht)

## Tests

```bash
make check
```

`check` ist der volle Prüflauf: Ruff (Lint und Format), Shellcheck, die
Doku-Prüfung und alle Tests. `make test ARGS="-k name"` lässt nur passende
Tests laufen, `make format` formatiert den Python-Code. Ohne `make setup`
brechen die Prüfungen mit einem Hinweis darauf ab.

Die Tests rufen den installierten Befehl `devtools` auf. pipx ist dabei ein
Ersatz im `PATH`, der seinen Stand in einer Datei im temporären Testordner
führt und jeden Aufruf protokolliert; das pipx des Rechners bleibt
unberührt. Ebenso ersetzt ein git-Ersatz `git ls-remote` und `git tag`: Er
liefert die Tags je Quelle aus der Variable `GIT_TAGS`, die Tests brauchen
kein Netz.

[↑ Übersicht](#übersicht)

## Übersetzungen

Sichtbare Texte stehen im Code englisch und laufen über `_()` aus
`src/mmit_devtools/i18n.py`, nie als roher String; Platzhalter sind benannt
(`{version}`). Die Sprache kommt aus `LANGUAGE`, `LC_ALL`, `LC_MESSAGES` oder
`LANG`; ohne Katalog erscheint der englische Text.

Die deutsche Übersetzung steht in
`src/mmit_devtools/locale/de/LC_MESSAGES/mmit-devtools.po`: msgid der
englische Text, msgstr der deutsche. Gepflegt wird die Datei von Hand: Neue
Einträge kommen ans Ende, Einträge ohne Text im Code werden gestrichen.
`make messages` sammelt alle Texte des Codes mit `pybabel extract` nach
`build/mmit-devtools.pot`, zum Vergleich. `pybabel update` läuft bewusst
nicht: Es sortiert die Datei um. Die Reihenfolge mit neuen Einträgen am Ende
lässt zwei Branches ohne Konflikt zusammenführen (`.gitattributes`).

Die `.mo` liegen nicht im Git. `make setup` übersetzt sie für die
Entwicklung, `setup.py` beim Paketbau in den Build-Ordner; so bringt auch
`pipx run --spec git+…` die deutschen Texte mit.

Tests halten den Stand: Jeder Text des Codes hat genau einen deutschen
Eintrag mit denselben Platzhaltern, keiner ist unscharf oder verwaist, und
kein Oberflächentext steht roh im Code.

[↑ Übersicht](#übersicht)

## Aufbau

| Datei | Aufgabe |
|---|---|
| `src/mmit_devtools/cli.py` | Befehl `devtools`: Argumente, Ausgabe je Werkzeug, Exit-Codes |
| `src/mmit_devtools/config.py` | `.dev-tools.conf.sh` lesen, Werkzeuge mit Paket, Tag, Quelle und Einbindung |
| `src/mmit_devtools/pipx.py` | Zugriff auf pipx: `pipx list --json` lesen, Installation aufrufen |
| `src/mmit_devtools/git.py` | Zugriff auf git: neuester Release-Tag einer Git-Quelle (`git ls-remote`) oder Arbeitskopie (`git tag`) |
| `src/mmit_devtools/sync.py` | Abgleich von Config und Installation: was zu tun ist und was geschah |
| `src/mmit_devtools/versions.py` | SemVer aus einem Tag, Version einer Arbeitskopie aus `pyproject.toml` |
| `src/mmit_devtools/style.py` | Ausgabe einer Zeile mit Rollen des CLI-Themes, Abschluss mit Leerzeile und Parser aus CLITheme; ohne das Extra `theme` reiner Text |
| `src/mmit_devtools/i18n.py` | `_()` über gettext, Kataloge unter `src/mmit_devtools/locale/` |
| `setup.py` | Paketbau: übersetzt die Kataloge beim Bauen nach `.mo` |

Der Einstiegspunkt `devtools` steht in `pyproject.toml` unter
`[project.scripts]`; darüber funktioniert auch `pipx run --spec … devtools`.

Was schutzwürdig ist, welche Befehle DevTools startet und wem es dabei
vertraut, steht im [Sicherheitsprofil](security-profile.md).

[↑ Übersicht](#übersicht)

## Version und Release

Die Version steht nur in `pyproject.toml`. `make version` zeigt sie samt
letztem Tag; ein Release erhöht sie, committet, taggt, pusht und schreibt
danach `CHANGELOG.md`:

```bash
make tag-patch MSG="Kurzbeschreibung"
```

`tag-minor` und `tag-major` arbeiten gleich. Die Targets brauchen BashLib
(`make hints`).

[↑ Übersicht](#übersicht)
