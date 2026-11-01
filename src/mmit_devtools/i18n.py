"""Sichtbare Texte über gettext; die msgid ist der englische Text.

Ohne Katalog erscheint der englische Text. Übersetzungen sind Kataloge unter locale/ (heute
de); die Sprache kommt wie üblich aus LANGUAGE, LC_ALL, LC_MESSAGES oder LANG. Kein
Oberflächentext als roher String: _() für Texte, Platzhalter benannt ({version}).
"""

import gettext
from pathlib import Path

LOCALE = Path(__file__).parent / "locale"
DOMAIN = "mmit-devtools"

_ = gettext.translation(DOMAIN, localedir=LOCALE, fallback=True).gettext
