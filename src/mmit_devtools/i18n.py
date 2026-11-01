"""Sichtbare Texte über gettext; die msgid ist der englische Text.

Ohne Katalog erscheint der englische Text. Übersetzungen sind Kataloge unter locale/ (heute
de); die Sprache kommt wie üblich aus LANGUAGE, LC_ALL, LC_MESSAGES oder LANG. Kein
Oberflächentext als roher String: _() für Texte, Platzhalter benannt ({version}).

DEVTOOLS_LOCALE_DIR nennt einen anderen Katalogordner; die Tests zeigen damit auf einen leeren
oder eigenen und hängen nicht davon ab, ob im Quellbaum eine .mo liegt.
"""

import gettext
import os
from pathlib import Path

LOCALE = Path(os.environ.get("DEVTOOLS_LOCALE_DIR") or Path(__file__).parent / "locale")
DOMAIN = "mmit-devtools"

_ = gettext.translation(DOMAIN, localedir=LOCALE, fallback=True).gettext
