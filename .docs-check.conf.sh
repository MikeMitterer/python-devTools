#!/usr/bin/env bash
# Config für docs-check.sh (ProjectTools) — wird gesourced, kein Custom-Parser.
# .sh-Endung fürs IDE-Highlighting. Format-Doku: ProjectTools/docs/tools/docs-check.md
# Anlegen/aktualisieren:  docs-check.sh --example > .docs-check.conf.sh
# shellcheck disable=SC2034  # von docs-check.sh gesourct

# Pfadangaben in DOCS, LINKS_ONLY, EXCLUDE, REQUIRED, CODE_VARIABLES,
# SCREENSHOTS, SCREENSHOTS_EXCLUDE, DEPENDS und DEPENDS_HINT: relativ zum Projekt-Root, führendes
# "./" erlaubt. Muster wie in .gitignore:
#   *    beliebige Zeichen innerhalb eines Ordners   docs/*.md
#   **   beliebig viele Ordner                       docs/**/*.md, **/README.md
#   ?    genau ein Zeichen                           docs/v?.md
# Ordner und Muster treffen nur Dateien, die git nicht ignoriert.

# ─── Welche Dokumente geprüft werden ───────────────────────────────────────────

# Inhaltlich zu prüfende Dokumente: Datei, Ordner (alle *.md darin) oder
# Muster. Ein Muster ohne Treffer ist ein Problem.
DOCS=(
    "README.md"
    "README.de.md"
    "docs"
)

# Interne Doku, die nur auf tote Links, fehlende Bilder und Anker geprüft
# wird, nicht auf verbotene Begriffe, Befehle oder Variablen. Gedacht für
# Projektregeln und Tickets, die interne Angaben nennen dürfen.
LINKS_ONLY=(
    "AGENTS.md"
    "CLAUDE.md"
)

# Aus DOCS und LINKS_ONLY ausgenommen: Datei, Ordner samt Inhalt oder Muster (ein Muster
# darf auch einen Ordner treffen, z. B. "docs/drafts-*"). Gedacht für
# datierte Entwürfe oder Vorlagen, die verbotene Begriffe bewusst nennen.
EXCLUDE=(
)

# ─── Was in den Dokumenten stehen darf ─────────────────────────────────────────

# Text, der in keinem Dokument aus DOCS stehen darf. Geprüft wird jede
# Zeile, auch in Codeblöcken; jeder Treffer ist ein Problem (Exit-Code 1).
# Die Meldung nennt Zeilen, gefundenen Text und den Grund.
#
# Ein Eintrag ist eine von zwei Formen, jeweils optional mit "|<grund>":
#
#   "<text>"             Genau dieser Text, Groß-/Kleinschreibung zählt.
#                        Trifft auch innerhalb von Wörtern: "UID" trifft
#                        "PUID".
#
#   "/<muster>/<flags>"  Regulärer Ausdruck in JavaScript-Syntax:
#                          \b        Wortgrenze: "/\bUID\b/" trifft nicht "PUID"
#                          (a|b)     Alternative: "/\bP(U|G)ID\b/"
#                          a|b       ganze Alternativen: "/PUID|nobody:users/"
#                          \d+       Ziffern: "/\b99:\d+\b/"
#                        Flags: i = Groß-/Kleinschreibung egal, u = Unicode.
#                        "|" im Muster ist erlaubt: Das Muster endet am
#                        ersten "/", dem nur Flags und dann "|" oder das
#                        Zeilenende folgen. Ein "/" im Muster wird "\/".
#                        Ein ungültiger Ausdruck bricht mit Exit-Code 2 ab.
#
# In Bash-Strings mit doppelten Anführungszeichen bleiben "\b" und "\d"
# erhalten; Dollarzeichen und Backticks brauchen einen Backslash davor.
#
# Ein Eintrag je Zusammenhang, damit jeder seinen eigenen Grund hat:
FORBIDDEN=(
    # Interne Umgebungsvariablen, in jeder Schreibweise
    # "/\bP(U|G)ID\b/i|interne Variablen, nicht in Nutzerdoku"
    # Standardnutzer als Zahl und als Name
    # "/\b99:100\b|\bnobody:users\b/i|Standard-IDs, nicht in Nutzerdoku"
    # EUPL-Pflichten nur mit Bedingung (Weitergabe, Netzwerkdienst)
    "/if you change or redistribute|wer \S+ ändert oder weitergibt|preserve the required notices/i|EUPL-Pflichten ohne Bedingung: Satz aus dem Lizenz-Baustein verwenden"
)

# Optional: höchstens so viele farbige Hinweisboxen (> [!WARNING] usw.) je
# Dokument. Leer oder nicht gesetzt: keine Grenze.
MAX_ALERTS=""

# ─── Variablen zwischen Doku und Code ──────────────────────────────────────────

# Variablen, die die Doku nennen darf, obwohl sie in keiner versionierten
# Datei vorkommen, z. B. aus einer eingebundenen, nicht versionierten
# Bibliothek. Je Eintrag optional mit "|<grund>".
KNOWN_VARIABLES=(
    "NAME_TAG|Platzhalter: NAME steht für das Präfix eines Werkzeugs in .dev-tools.conf.sh"
    "NAME_SOURCE|Platzhalter: NAME steht für das Präfix eines Werkzeugs in .dev-tools.conf.sh"
    "NAME_EDITABLE|Platzhalter: NAME steht für das Präfix eines Werkzeugs in .dev-tools.conf.sh"
    "NAME_LABEL|Platzhalter: NAME steht für das Präfix eines Werkzeugs in .dev-tools.conf.sh"
)

# Make-Targets, die die Doku nennen darf, obwohl kein Makefile im Projekt sie
# enthält, z. B. aus einer nicht versionierten Bibliothek (MakeLib unter .libs/).
# Je Eintrag "TARGET" optional mit "|<grund>"; gilt in jedem Verzeichnis mit Makefile.
KNOWN_MAKE_TARGETS=(
    # "dev-up|aus MakeLib, über .libs/MakeLib eingebunden"
)

# Optional: Code (Datei, Ordner oder Muster), dessen Umgebungsvariablen
# dokumentiert sein müssen. Jede Variable, die der Code dort ausdrücklich
# liest (process.env.X, os.environ["X"], getenv("X") u. a.), muss in einem
# Dokument aus DOCS stehen; sonst ist das ein Problem. Tests zählen nicht.
CODE_VARIABLES=(
    "src"
)

# Vom Code gelesen, aber bewusst nicht dokumentiert, je mit "|<grund>".
INTERNAL_VARIABLES=(
    "DEVTOOLS_LOCALE_DIR|nur für die Tests: anderer Katalogordner statt der .mo im Paket"
)

# ─── Dateien, die es geben muss ────────────────────────────────────────────────

# Dateien, die es geben muss, je optional mit "|<grund>". Sie zählen nur,
# wenn sie versioniert und nicht leer sind; .md-Dateien brauchen mindestens
# eine Überschrift ("# Titel").
#   "LICENSE"             ohne "/": irgendwo im Projekt
#   "./README.md"         mit "/": genau dort, "./" heißt Projekt-Root
#   "./docs/**/*.md"      Muster: mindestens ein Treffer
REQUIRED=(
    "README.md"
    "README.de.md"
    "LICENSE"
    "LICENSE.de.txt"
    "LICENSING.md"
)

# ─── Abhängige Dateien und Screenshots ─────────────────────────────────────────

# Abhängige Dateien müssen ihrer Basis folgen: Screenshots dem UI-Code,
# Übersetzungen und Kurzfassungen ihrem Original, erzeugte Dateien ihrer
# Quelle. Ändert sich die Basis nach der abhängigen Datei, meldet die Prüfung
# das. Maßgeblich ist der letzte Commit laut git, uncommittete Änderungen
# zählen als jetzt; Dateidatum und Tagesdatum zählen nicht.
#
# Quittieren statt sinnlos anfassen: Verlangt eine Änderung der Basis nichts
# (Tippfehler im README, Codeänderung ohne sichtbare Folge), die Meldung aus
# SCREENSHOTS, DEPENDS oder DEPENDS_HINT nach dem Prüfen quittieren:
#
#   docs-check.sh --ack docs/images/dashboard.png
#   docs-check.sh --ack docs/images   # ganzer Ordner
#   docs-check.sh --ack               # alle offenen
#
# Das schreibt je Paar den letzten Commit der Basis nach .docs-check.ack; die
# Datei mitcommitten. Die Quittung gilt, bis die Basis einen neueren Commit
# hat, dann kommt die Meldung zurück. Nicht quittieren lassen sich Einträge mit
# Frist 0 (neu erzeugen) und uncommittete Basen (erst committen).

# Optional: Screenshots und der UI-Code, den sie zeigen, je
# "<ui-code>|<bilder>|<grund>". UI-Code: Datei, Ordner oder Muster, mehrere
# mit Komma; Bilder: Datei, Ordner oder Muster (ohne von git ignorierte).
# Hat sich der UI-Code nach einem Bild geändert, erscheint ein Hinweis; die
# Prüfung scheitert daran nicht.
SCREENSHOTS=(
)

# Optional: Bilder aus SCREENSHOTS, deren Alter keine Rolle spielt, etwa
# Logos, Diagramme oder Aufnahmen fremder Oberflächen: Datei, Ordner oder
# Muster wie in EXCLUDE. Sie müssen vorhanden sein, mit dem UI-Code verglichen
# werden sie nicht. Eine Ausnahme ohne Bild ist ein Problem.
SCREENSHOTS_EXCLUDE=(
    # "docs/images/logo.png"
)

# Optional: Dateien, die einer anderen bald nach deren Änderung folgen müssen,
# je "<basis>|<abhängig>|<tage>|<grund>" (z. B. Übersetzung oder erzeugte
# Vorschau). Ändert sich die Basis nach der abhängigen Datei, ist das ein
# Hinweis, nach <tage> Tagen ein Problem; 0 heißt: im selben Commit. Die Basis
# darf ein Ordner, ein Muster oder eine Liste mit Komma sein.
DEPENDS=(
    "README.md|README.de.md|3|deutsche Fassung"
)

# Gleiches Format, auch überfällig nur ein Hinweis: für Basen, die sich oft
# ändern, ohne dass die abhängige Datei etwas nachziehen muss.
DEPENDS_HINT=(
)

# Optional: Sprachfassungen mit derselben Gliederung, je
# "<original>|<übersetzung>|<grund>". Verglichen werden die Überschriften und
# je Abschnitt Linkziele, Bilder, Inline-Code, Codeblöcke (Mermaid nur als
# Anzahl), Hinweisboxen und Absätze. Fehlt in einer Fassung ein Teil, ist das
# ein Problem. Den übersetzten Text selbst prüft das nicht.
TRANSLATIONS=(
    "README.md|README.de.md|deutsche Fassung"
)
