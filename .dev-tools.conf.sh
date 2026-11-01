#!/usr/bin/env bash
# Versionen der Entwicklungswerkzeuge, die dieses Projekt über pipx braucht.
# Das Makefile bindet die Datei mit include ein; Bash kann sie sourcen.
# Deshalb NAME=wert ohne Anführungszeichen und ohne Leerzeichen um das =.
# shellcheck disable=SC2034  # vom Makefile gelesen

# ProjectTools (docs-check, repo-status). pipx braucht den vollen Release-Tag;
# die Mindestversion ist dessen SemVer-Teil (make info, make hints).
PROJECTTOOLS_TAG=v0.3.2+261029.1600.c7bbd
