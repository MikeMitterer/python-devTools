#!/usr/bin/env bash
# Entwicklungswerkzeuge, die dieses Projekt über pipx braucht, im Format von devtools
# (README, Abschnitt Config file): je Werkzeug NAME_PACKAGE, NAME_TAG, NAME_SOURCE und
# optional NAME_LABEL und NAME_EDITABLE. Das Makefile bindet die Datei mit include ein; Bash
# kann sie sourcen. Deshalb NAME=wert ohne Anführungszeichen und ohne Leerzeichen um das =.
# shellcheck disable=SC2034  # vom Makefile gelesen

# ProjectTools (docs-check, repo-status, changelog). pipx braucht den vollen Release-Tag;
# die Mindestversion ist dessen SemVer-Teil (make info, make hints).
PROJECTTOOLS_PACKAGE=mmit-projecttools
PROJECTTOOLS_LABEL=ProjectTools
PROJECTTOOLS_TAG=v0.3.2+261029.1600.c7bbd
PROJECTTOOLS_SOURCE=git+https://github.com/MikeMitterer/bash-ProjectTools.git

# BashLib (version und tag-* im Makefile). Wer BashLib selbst ändert,
# installiert die Arbeitskopie mit pipx install -e; dann gilt die Version dort.
BASHLIB_PACKAGE=mmit-bashlib
BASHLIB_LABEL=BashLib
BASHLIB_TAG=v0.1.0
BASHLIB_SOURCE=git+https://github.com/MikeMitterer/bash-lib.git
