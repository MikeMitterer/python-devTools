<div align="center">

# DevTools

**Entwicklungswerkzeuge eines Projekts mit pipx prüfen, zeigen und installieren**

[Beispiel](#beispiel) · [Schnellstart](#schnellstart) · [Config-Datei](#config-datei) · [Befehle](#befehle) · [Entwicklung](docs/development.md)

[English](README.md) · Deutsch

</div>

DevTools liest die Entwicklungswerkzeuge, die ein Projekt braucht, aus seiner
`.dev-tools.conf.sh`: je Werkzeug das pipx-Paket, den Release-Tag und die
Quelle, eine Git-URL oder eine lokale Arbeitskopie. Der Befehl `devtools`
zeigt, was installiert ist, bringt jedes Werkzeug mit pipx auf Quelle und Tag
und prüft die Mindestversion, in jedem Projekt gleich statt in jedem
Makefile neu.

## Übersicht

- [Beispiel](#beispiel)
- [Funktionen](#funktionen)
- [Schnellstart](#schnellstart)
- [Config-Datei](#config-datei)
- [Befehle](#befehle)
- [Entwicklung](#entwicklung)
- [Lizenz](#lizenz)

## Beispiel

```console
$ devtools install
  ProjectTools  current (0.3.2)
  BashLib       updated from 0.1.0 to 0.2.0 (git+https://github.com/MikeMitterer/bash-lib.git)
```

Eine Zeile je Werkzeug: aktuell, aktualisiert von einer Version auf eine
andere, installiert oder Arbeitskopie. Die Ausgabe ist englisch wie hier oder
deutsch, je nach Spracheinstellung (`LANGUAGE`, `LC_ALL`, `LANG`).

[↑ Übersicht](#übersicht)

## Funktionen

- **Eine Config-Datei:** Werkzeuge, pipx-Pakete, Tags und Quellen in
  `.dev-tools.conf.sh`, die auch Make und Bash lesen.
- **Git oder Arbeitskopie:** Ein Werkzeug kommt aus einer Git-URL zum Tag
  oder aus einem lokalen Checkout, bearbeitbar (`pipx install -e`) oder als
  fester Stand.
- **Arbeitskopien bleiben:** Hast du selbst eine Arbeitskopie installiert,
  während die Config Git verlangt, lässt `devtools install` sie stehen und
  sagt das.
- **Richtige Version einer Arbeitskopie:** pipx friert die Paketversion einer
  bearbeitbaren Installation ein; DevTools liest die Version stattdessen aus
  der `pyproject.toml` der Arbeitskopie.
- **Auf den neuesten Release:** `devtools upgrade` sucht je Quelle den
  neuesten Release-Tag, vom Git-Remote oder aus dem Repo der Arbeitskopie,
  und installiert ihn; `-n` zeigt installierte, Config- und neueste Version
  nebeneinander, `--write` trägt die neueren Tags in die Config ein.
- **Prüfung der Mindestversion:** `devtools check NAME` scheitert mit dem
  Installationsbefehl, passend für ein Makefile.
- **Nur Standardbibliothek:** Python 3.14 oder neuer, zur Laufzeit keine
  weiteren Pakete.
- **Farben auf Wunsch:** Mit dem Extra `theme` übernimmt die Ausgabe die
  Farben des gemeinsamen
  [CLITheme](https://github.com/MikeMitterer/python-clitheme), nur im
  Terminal und nie mit `NO_COLOR`, und jede Ausgabe samt Hilfe endet wie in
  allen Apps mit CLITheme mit einer Leerzeile; ohne das Extra bleibt sie reiner
  Text.

[↑ Übersicht](#übersicht)

## Schnellstart

Voraussetzungen: Python 3.14 oder neuer und [pipx](https://pipx.pypa.io/).

Tags folgen dem Schema `vX.Y.Z+YYMMDD.HHMM.hash`, und pipx braucht den vollen
Tag. Dieser Befehl zeigt den neuesten:

```bash
git ls-remote --tags --refs --sort=-v:refname https://github.com/MikeMitterer/python-devtools.git | head -1
```

**Ohne Installation:** DevTools im Projektordner direkt aus Git starten,
`<release-tag>` durch den Tag ersetzen:

```bash
pipx run --spec 'git+https://github.com/MikeMitterer/python-devtools.git@<release-tag>' devtools status
```

**Installiert:** einmal installieren, danach `devtools` in jedem Projekt
benutzen.

```bash
pipx install 'git+https://github.com/MikeMitterer/python-devtools.git@<release-tag>'
devtools install
```

**Aus einem Checkout:** `make install` baut DevTools aus dem ausgecheckten Stand
und installiert es mit pipx, samt Farben. `make install-tools` installiert
dagegen die Werkzeuge aus `.dev-tools.conf.sh`.

**Mit Farben:** Das Extra `theme` installiert zusätzlich CLITheme und rich.

```bash
pipx install 'mmit-devtools[theme] @ git+https://github.com/MikeMitterer/python-devtools.git@<release-tag>'
```

[↑ Übersicht](#übersicht)

## Config-Datei

`devtools` liest `.dev-tools.conf.sh` im aktuellen Ordner; `--config`
nennt eine andere Datei. Jede Zeile ist `NAME=value` ohne Anführungszeichen und ohne
Leerzeichen um das `=`, damit Make die Datei einbinden und Bash sie sourcen
kann. `#` beginnt einen Kommentar. Jedes `NAME_PACKAGE` macht `NAME` zu einem
Werkzeug; die übrigen Einträge tragen dasselbe Präfix.

```bash
PROJECTTOOLS_PACKAGE=mmit-projecttools
PROJECTTOOLS_LABEL=ProjectTools
PROJECTTOOLS_TAG=v0.3.2+261029.1600.c7bbd
PROJECTTOOLS_SOURCE=git+https://github.com/MikeMitterer/bash-ProjectTools.git
PROJECTTOOLS_EDITABLE=yes
```

| Eintrag | Pflicht | Bedeutung |
|---|---|---|
| `NAME_PACKAGE` | ja | pipx-Paket des Werkzeugs, etwa `mmit-projecttools` |
| `NAME_TAG` | ja | Release-Tag; sein Teil `X.Y.Z` ist die Mindestversion |
| `NAME_SOURCE` | ja | Git-URL (installiert zum Tag) oder Pfad einer Arbeitskopie, relativ zur Config-Datei |
| `NAME_EDITABLE` | nein | Für eine Arbeitskopie: `yes` bindet sie bearbeitbar ein (`pipx install -e`), `no` als festen Stand; Vorgabe `yes` |
| `NAME_LABEL` | nein | Name in der Ausgabe; Vorgabe der Paketname |

**Gepinnter Tag:** `NAME_TAG` und `NAME_SOURCE` ohne `NAME_PACKAGE` halten
einen Tag fest, den DevTools nicht installiert, etwa die Version, die ein
Makefile mit `pipx run` startet. `devtools upgrade` zeigt seinen neuesten Tag
und schreibt ihn mit `--write`; die übrigen Befehle übergehen ihn. Ohne
`NAME_SOURCE` lässt sich der neueste Tag nicht finden.

```bash
DEVTOOLS_TAG=v0.2.0+261101.1319.09840
DEVTOOLS_SOURCE=git+https://github.com/MikeMitterer/python-devtools.git
```

[↑ Übersicht](#übersicht)

## Befehle

| Befehl | Tut |
|---|---|
| `devtools status` | Zeigt je Werkzeug den Stand und was `install` tun würde; installiert nichts |
| `devtools install` | Installiert fehlende oder ältere Werkzeuge aus Quelle und Tag (`pipx install --force`) |
| `devtools upgrade [NAME]` | Installiert je Quelle den neuesten Release-Tag; `-n` (`--dry-run`) zeigt nur installierte, Config- und neueste Version, `--write` schreibt die neueren Tags auch in die Config |
| `devtools check NAME` | Exit 0, wenn die installierte Version die des Tags erreicht, sonst Exit 1 mit dem Installationsbefehl |
| `devtools command NAME` | Gibt den Installationsbefehl des Werkzeugs aus |

`NAME` ist das Präfix der Einträge in Kleinbuchstaben, etwa `projecttools`.
`devtools --help` zeigt alle Optionen.

`upgrade` nimmt Release-Tags der Form `vX.Y.Z`, wahlweise mit Build-Teil wie
`+261031.2038.b22f0`; andere Tags und Vorabversionen zählen nicht. Bei einer
Git-Quelle fragt es das Remote (`git ls-remote`), bei einer Arbeitskopie die
Tags ihres Repos; die Arbeitskopie selbst holt und ändert es nie, und ohne
lesbaren Tag bleibt sie einfach beim Tag der Config. Eine
bearbeitbare Arbeitskopie ist schon live eingebunden, dort gibt es nichts zu
installieren. Ist eine Quelle nicht lesbar, nennt die Zeile den Grund, die
übrigen Werkzeuge laufen weiter, und `upgrade` endet mit Exit 1.

Mit `--write` trägt `upgrade` die neueren Tags in die Config ein und nennt je
`NAME_TAG`, was geschah: alt → neu, aktuell oder warum er bleibt. Den Tag
eines Werkzeugs schreibt es nur, wenn die installierte Version ihn danach
erreicht, sonst scheiterte `devtools check`. Ohne `--write` bleibt die Config,
wie sie ist; die Ausgabe sagt dann, dass sie noch ältere Tags nennt. Ein
`NAME_TAG` ohne `NAME_SOURCE` bekommt eine eigene Zeile, weil sein neuester
Tag unbekannt ist. Steht DevTools selbst in der Config, kommt es zuletzt dran,
weil pipx dabei die Umgebung ersetzt, aus der es läuft.

[↑ Übersicht](#übersicht)

## Entwicklung

Einrichten aus dem Checkout, Tests und Releases beschreibt die
[Entwicklerdoku](docs/development.md).

[↑ Übersicht](#übersicht)

## Lizenz

Copyright © 2026 Michael Mitterer. **MangoLila GmbH** ist Anbieterin und
Lizenzgeberin.

DevTools steht unter der **[EUPL 1.2](LICENSE)**, nur Version 1.2. Sie
erlaubt private und gewerbliche Nutzung, Änderungen, Weitergabe, Verkauf und
Hosting ohne kostenpflichtige Lizenz.

Wer DevTools oder eine geänderte Fassung weitergibt oder als Netzwerkdienst
anbietet, muss die Urheber- und Lizenzhinweise erhalten, Änderungen
kennzeichnen und den zugehörigen Quelltext nach den Copyleft-Regeln der
Lizenz bereitstellen.

Die Gewährleistungs- und Haftungsausschlüsse der EUPL-Artikel 7 und 8 gelten
auch gegenüber Verbrauchern, soweit das Gesetz es zulässt. Zwingende Rechte
bleiben unberührt, darunter die Haftung für Vorsatz, grobe Fahrlässigkeit,
Personenschäden und nach dem Produkthaftungsgesetz. Eine zusätzliche Garantie
wird nicht übernommen.

Kontakt: **office@MangoLila.at**.

Details: [LICENSE](LICENSE) · [Deutscher Lizenztext](LICENSE.de.txt) ·
[Anbieter- und Verbrauchererklärung](LICENSING.md)

[↑ Übersicht](#übersicht)
