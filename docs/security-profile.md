# Sicherheitsprofil

Was in diesem Projekt schutzwürdig ist und welche Grundsatzentscheidungen
gelten. Ein Konzeptticket, das den Aufbau der App berührt, prüft und ergänzt
es. Bei jedem Code-Ticket prüfen Implementer und Reviewer den Diff dagegen
(Guard `security`, Bericht ist Pflicht).
Leere Abschnitte heißen „noch nicht entschieden“; „keine“ ist eine Entscheidung.

DevTools ist ein lokales Kommandozeilenwerkzeug: Es liest `.dev-tools.conf.sh`
eines Projekts, fragt pipx und git und installiert Werkzeuge mit pipx.

## Sensible Daten

Keine eigenen. DevTools verarbeitet nur Paketnamen, Tags, Quellen (Git-URLs
oder Pfade) und Versionen. Eine Git-URL mit eingebetteten Zugangsdaten
(`https://name:token@…`) wäre schutzwürdig; sie gehört nicht in die Config,
weil DevTools Quellen in seiner Ausgabe nennt und die Config im Repository
liegt.

## Speicherorte

- **Config:** DevTools schreibt nur mit `devtools upgrade --write` in
  `.dev-tools.conf.sh` und ändert dort nur den Wert vorhandener
  `NAME_TAG`-Einträge; alle übrigen Zeichen bleiben.
- **Installationen:** Die venvs verwaltet pipx in seinen eigenen Ordnern.
- **Logs und Zwischenstände:** keine. Der Befehl `devtools` legt keine Dateien
  an und speichert nichts zwischen.
- **make install:** baut in einem temporären Ordner, den es danach löscht, und
  legt das Wheel unter `${XDG_CACHE_HOME:-~/.cache}/mmit-devtools/` ab. Dort
  löscht es nur ältere `mmit_devtools-*.whl`, sonst nichts; Ordner aus
  Variablen des Aufrufers löscht es nie.

## Geheimnisse

Keine. DevTools liest weder Umgebungsdateien noch Schlüssel. Ein Remote, das
eine Anmeldung verlangt, erreicht git über die eigene Einrichtung des
Rechners (SSH-Schlüssel, Credential-Helper). DevTools startet git mit
`GIT_TERMINAL_PROMPT=0`; fehlt die Anmeldung, scheitert der Aufruf, statt
nach einem Kennwort zu fragen.

## Anmeldung

Keine. DevTools ist ein lokaler Befehl ohne Benutzer, Sitzungen oder Tokens;
es läuft mit den Rechten dessen, der es aufruft.

## Zugriffe von außen

- **Config:** Eine Datei des Projekts und damit so vertrauenswürdig wie das
  Projekt selbst. Ihre Werte gehen nur als einzelne Argumente an pipx und git,
  nie in eine Shell. Relative Pfade gelten ab dem Ordner der Config.
- **Quellen:** Wer eine Quelle in die Config einträgt, vertraut ihr. pipx
  baut und installiert das Paket der Quelle; dabei läuft Code aus diesem
  Repository.
- **Tags von Remotes und Arbeitskopien:** `devtools upgrade` übernimmt nur
  Tags, die dem Muster `vX.Y.Z` mit optionalem Build-Teil aus Ziffern,
  Buchstaben und Punkten entsprechen. Andere Tags verwirft es, bevor sie einen
  pipx-Aufruf oder eine Zeile der Config bilden. Wer in ein Quell-Repository
  Tags schreiben darf, bestimmt damit, was `upgrade` installiert.
- **Abhängigkeiten:** ohne Extras keine. Das Extra `theme` installiert
  `mmit-cli-theme` an einem festen Git-Tag und dazu rich aus dem Paketindex.
  Es liest das Theme aus `${XDG_CONFIG_HOME:-~/.config}/cli-theme/` und die
  Variablen `CLI_THEME`, `NO_COLOR` und `TERM`; daraus entstehen nur Farben,
  nie Befehle oder Pfade für pipx und git.
- **pipx list --json:** wird als JSON gelesen; ein unlesbarer Stand endet mit
  einer Meldung statt eines Tracebacks.

## Ausführung

- **Befehle:** nur `pipx` (`list --json`, `install --force`) und `git`
  (`ls-remote --tags --refs`, `-C PFAD tag --list`), jeweils über den `PATH`.
  Die Argumente legt DevTools fest; aus der Config kommen nur Paketquelle,
  Tag und Pfad.
- **Keine Shell:** Aufrufe laufen als Argumentliste über `subprocess.run`.
- **Exit-Codes:** werden geprüft. Scheitert pipx oder git, nennt die Zeile des
  Werkzeugs den Grund und DevTools endet mit Exit 1.
- **Zeitgrenze:** git-Aufrufe brechen nach 60 Sekunden ab; pipx-Aufrufe haben
  keine Zeitgrenze, weil ein Paketbau lange dauern kann.
- **Eigene Umgebung:** Steht DevTools selbst in der Config, installiert pipx
  es zuletzt, weil es dabei die venv ersetzt, aus der der Lauf kommt.
