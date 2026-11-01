SHELL := bash

.DEFAULT_GOAL := help

# CURDIR statt $(realpath $(shell pwd)): Make-Funktionen wie realpath und notdir zerlegen einen
# Pfad mit Leerzeichen in Wörter.
WORKSPACE    := $(CURDIR)
# Der Checkout-Pfad gequotet, zum Kopieren in einen angezeigten Befehl und für $(shell …).
WORKSPACE_SQ := '$(subst ','\'',$(WORKSPACE))'
PROJECT_NAME := $(shell basename -- $(WORKSPACE_SQ))
# Werte von außen nur über die Umgebung in Rezepte geben ("$${WORKSPACE}"): ein $(…), Backtick
# oder Apostroph im Checkout-Pfad wertete die Shell sonst aus.
export WORKSPACE WORKSPACE_SQ PROJECT_NAME MSG

# Paket, Release-Tag und Quelle der pipx-Werkzeuge stehen nur in .dev-tools.conf.sh (Format von
# devtools). Prüfen, zeigen und installieren übernimmt devtools (DEVTOOLS unten); selbst
# entwickelt: make hints.

# BashLib für version und tag-* (Maintainer): ein von außen gesetztes BASH_LIBS geht vor,
# sonst bashlib-path aus der pipx-Installation. Die Version prüft devtools in beiden Fällen.
ifndef BASH_LIBS
BASH_LIBS := $(shell bashlib-path 2>/dev/null)
endif
export BASH_LIBS

# Liste der Makefiles unausgewertet über die Umgebung; DEV_MAKE kommt von außen.
export HELP_FILES = $(value MAKEFILE_LIST)

-include ${DEV_MAKE}/colours.mk

# Fallbacks, wenn MakeLib nicht verfügbar ist (DEV_MAKE nicht gesetzt)
YELLOW ?= $(shell printf "\033[38;5;3m")
GREEN  ?= $(shell printf "\033[38;5;2m")
BLUE   ?= $(shell printf "\033[38;5;6m")
RED    ?= $(shell printf "\033[38;5;1m")
RESET  ?= $(shell printf "\033[0m")
THEME_COLOR_GROUP   ?= $(YELLOW)
THEME_COLOR_TARGET  ?= $(BLUE)
THEME_COLOR_DESC    ?= $(GREEN)
THEME_COLOR_DANGER  ?= $(RED)
THEME_INDENT_GROUP  ?= $(shell printf '%2s' '')
THEME_INDENT_TARGET ?= $(shell printf '%7s' '')
THEME_WIDTH_TARGET  ?= 22
THEME_COLUMN_GAP    ?= 1

# Kennzeichnet in der Hilfe Targets, die BashLib brauchen; ihre Beschreibung endet auf „— Maintainer“.
MAINTAINER_MARK = $(THEME_COLOR_DANGER)[Maintainer]$(THEME_COLOR_DESC)

# Entwicklungs-venv mit der neuesten stabilen Python-Version; PYTHON_BOOTSTRAP=… überschreibt.
PYTHON_BOOTSTRAP ?= python3.14
VENV   := .venv
PYTHON := $(VENV)/bin/python
RUFF   := $(VENV)/bin/ruff
# pybabel über Python statt über sein Skript: pip schreibt in Skripte eine sh-Zeile, die einen
# Checkout-Pfad mit $(…) auswerten würde.
PYBABEL := $(PYTHON) -m babel.messages.frontend
# devtools aus der .venv (make setup), ebenfalls über Python. Der pre-commit-Hook prüft in einer
# Kopie ohne .venv und nennt den Interpreter in DEVTOOLS_PYTHON; als Wert von außen nur über die
# Umgebung gelesen ("$${…}").
DEVTOOLS     = "$${DEVTOOLS_PYTHON:-$(PYTHON)}" -m mmit_devtools.cli
HAS_DEVTOOLS = "$${DEVTOOLS_PYTHON:-$(PYTHON)}" -c 'import mmit_devtools' 2>/dev/null
NO_DEVTOOLS  = echo -e "  $(RED)✗$(RESET) devtools fehlt, erst einrichten: $(YELLOW)make setup$(RESET)" >&2; exit 1
# Was setup herstellt und require-setup prüft: Paket und Werkzeuge in der .venv und die .mo.
CATALOGS     := $(patsubst %.po,%.mo,$(wildcard src/mmit_devtools/locale/*/LC_MESSAGES/*.po))
SETUP_STAMPS := $(VENV)/.installed $(CATALOGS)
SHELL_FILES := .githooks/pre-commit .dev-tools.conf.sh .docs-check.conf.sh .repo-status.conf.sh

# ─── Hilfe ───────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Alle verfügbaren Befehle anzeigen
	@echo
	@echo "Please use \`make <$(THEME_COLOR_GROUP)target$(RESET)>' where <target> is one of"
	@echo
	@echo "Project: $(THEME_COLOR_GROUP)$${PROJECT_NAME}$(RESET)"
	@echo
	@set -o pipefail; grep -hE '^(##@|[a-zA-Z0-9_-]+:.*?## )' $${HELP_FILES} | \
	  awk 'BEGIN {FS = ":.*?## "}; \
	    /^##@/ { printf "\n$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)%s$(RESET)\n", substr($$0, 5); next }; \
	    { desc = $$2; sub(/ — Maintainer$$/, " $(MAINTAINER_MARK)", desc); \
	      printf "$(THEME_INDENT_TARGET)$(THEME_COLOR_TARGET)%-$(THEME_WIDTH_TARGET)s%$(THEME_COLUMN_GAP)s$(THEME_COLOR_DESC)%s$(RESET)\n", $$1, "", desc }'
	@echo

.PHONY: info
info: ## Umgebung, Pfade und Werkzeugversionen anzeigen
	@echo
	@printf "    $(YELLOW)%-16s$(RESET) = $(BLUE)%s$(RESET)\n" \
		PROJECT_NAME "$${PROJECT_NAME}" \
		WORKSPACE "$${WORKSPACE}" \
		PYTHON_BOOTSTRAP '$(PYTHON_BOOTSTRAP)' \
		VENV '$(VENV)' \
		BASH_LIBS "$${BASH_LIBS:-nicht gesetzt}" \
		DEV_MAKE "$${DEV_MAKE:-nicht gesetzt}"
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Werkzeuge (.dev-tools.conf.sh)$(RESET)"
	@if $(HAS_DEVTOOLS); then $(DEVTOOLS) status || true; else echo "  devtools noch nicht eingerichtet: make setup"; fi
	@echo

# Repo-Adresse aus git remote origin (SSH oder HTTPS) als https-URL, und der letzte Release-Tag.
# Beide kommen von außen (Ref-Namen dürfen $, ( und ) enthalten) und landen im Rezept; deshalb
# gelten sie nur aus erlaubten Zeichen, sonst leer.
REPO_URL    := $(shell git remote get-url origin 2>/dev/null | sed -E 's|^git@([^:]+):|https://\1/|; s|\.git$$||' | grep -xE '[A-Za-z0-9._:/@+~-]+')
RELEASE_TAG := $(or $(shell git describe --tags --abbrev=0 2>/dev/null | grep -xE '[A-Za-z0-9._+-]+'),vX.Y.Z)
NO_REMOTE   := kein Remote origin (git remote add origin …)

# Eine Zeile für hints: Beschriftung auf THEME_WIDTH_TARGET Zeichen aufgefüllt, dann der Wert.
# printf füllt nach Bytes auf; gezählt werden deshalb Zeichen (UTF-8-Folgebytes nicht).
# Aufruf: $(call hint_row,Beschriftung,Wert), ohne Komma in den Werten.
hint_row = label="$(1)"; \
	chars=$$(printf '%s' "$$label" | LC_ALL=C tr -d '\200-\277' | wc -c); \
	printf "$(THEME_INDENT_TARGET)$(THEME_COLOR_TARGET)%s$(RESET)%*s$(THEME_COLOR_DESC)%s$(RESET)\n" \
		"$$label" $$(( $(THEME_WIDTH_TARGET) - chars + $(THEME_COLUMN_GAP) )) "" "$(2)"

# Setzt in der Shell checkout auf den pipx-Befehl für die Arbeitskopie eines Werkzeugs, dessen
# Ordner in der Umgebungsvariable $(1) steht (etwa PROJECT_TOOLS), gequotet zum Kopieren; sonst
# ein Hinweis. Arbeitskopie heißt: An der Git-Wurzel liegt das Paket $(2). Die Git-Wurzel allein
# genügt nicht, eine pipx-Installation in einem Home unter Git hätte sonst das Home als Wurzel.
# Leer gelassen fiele git -C auf den aktuellen Ordner zurück.
tool_checkout = top=""; [[ -n "$${$(1):-}" ]] && top=$$(git -C "$${$(1)}" rev-parse --show-toplevel 2>/dev/null); \
	if [[ -n "$$top" ]] && grep -qx 'name = "$(2)"' "$$top/pyproject.toml" 2>/dev/null; then \
		checkout="pipx install -e '$$(printf '%s' "$$top" | sed "s/'/'\\\\''/g")'"; \
	else checkout="keine Arbeitskopie über $(1)"; fi

.PHONY: hints
hints: ## Reihenfolge für den ersten Start und Installationswege anzeigen
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Erster Start$(RESET)"
	@$(call hint_row,1. Einrichten,make setup)
	@$(call hint_row,2. Prüfen,make check)
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)devtools benutzen$(RESET)"
	@$(call hint_row,Aus Git,$(if $(REPO_URL),pipx install 'git+$(REPO_URL).git@$(RELEASE_TAG)',$(NO_REMOTE)))
	@$(call hint_row,Ohne Installation,$(if $(REPO_URL),pipx run --spec 'git+$(REPO_URL).git@$(RELEASE_TAG)' devtools status,$(NO_REMOTE)))
	@$(call hint_row,Arbeitskopie,pipx install -e $${WORKSPACE_SQ})
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Werkzeuge$(RESET)"
	@$(call hint_row,Alle,make install-tools)
	@cmd=$$($(DEVTOOLS) command projecttools 2>/dev/null) || cmd="nach make setup: make hints"; $(call hint_row,ProjectTools,$$cmd)
	@cmd=$$($(DEVTOOLS) command bashlib 2>/dev/null) || cmd="nach make setup: make hints"; $(call hint_row,BashLib (Maintainer),$$cmd)
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Werkzeuge selbst entwickeln$(RESET)"
	@$(call tool_checkout,PROJECT_TOOLS,mmit-projecttools); $(call hint_row,ProjectTools,$$checkout)
	@$(call tool_checkout,BASH_LIBS,mmit-bashlib); $(call hint_row,BashLib,$$checkout)
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Links$(RESET)"
	@$(call hint_row,Repository,$(or $(REPO_URL),$(NO_REMOTE)))
	@echo

# ─── Precheck ────────────────────────────────────────────────────────────────

# Ohne Hilfeeintrag: läuft vor version und tag-*. Verlangt eine lesbare BashLib und die Mindestversion
# aus .dev-tools.conf.sh, auch bei BASH_LIBS von außen; nennt sonst den Installationsweg. Ist die
# Arbeitskopie hinter BASH_LIBS bearbeitbar mit pipx installiert, zählt ihre pyproject.toml.
.PHONY: precheck
precheck:
	@test -r "$${BASH_LIBS}/version.lib.sh" || { \
		echo -e "  $(RED)✗$(RESET) Nur für Maintainer: benötigt BashLib ($(YELLOW)BASH_LIBS$(RESET)): $(YELLOW)make install-tools$(RESET)" >&2; \
		exit 1; }
	@$(HAS_DEVTOOLS) || { $(NO_DEVTOOLS); }; $(DEVTOOLS) check bashlib

# Ohne Hilfeeintrag: verlangt ProjectTools in der Mindestversion aus .dev-tools.conf.sh; devtools
# nennt sonst den Installationsbefehl.
.PHONY: require-tools
require-tools:
	@$(HAS_DEVTOOLS) || { $(NO_DEVTOOLS); }; $(DEVTOOLS) check projecttools

# ─── Setup ───────────────────────────────────────────────────────────────────

##@ Setup

# Der einzige Einrichtungsweg, auch für agent-lessons (worktree_setup). Wiederholbar: die .venv
# gleicht er nur ab, wenn pyproject.toml neuer ist als die Stempeldatei.
.PHONY: setup
setup: $(SETUP_STAMPS) ## Git-Hooks, .venv mit dem Paket und den Prüfwerkzeugen, Übersetzungen einrichten; zeigt den Stand der Werkzeuge
	@git config core.hooksPath .githooks   # pre-commit: make docs-check
	@# Nur zeigen, nichts installieren: setup läuft auch in Workspaces und im Prüf-Worktree.
	@$(DEVTOOLS) status || echo -e "  $(YELLOW)⚠$(RESET) Stand der Werkzeuge nicht lesbar (make hints)"

# Werkzeuge auf Quelle und Tag aus .dev-tools.conf.sh; eine selbst installierte Arbeitskopie bleibt.
.PHONY: install-tools
install-tools: require-setup ## Werkzeuge aus .dev-tools.conf.sh mit pipx installieren oder aktualisieren
	@$(DEVTOOLS) install

# Stempeldatei: nur setup legt sie an. Nicht .venv/bin/python als Ziel nehmen; es ist ein Link
# aufs System-Python und hätte dessen Zeitstempel.
$(VENV)/.installed: pyproject.toml
	@command -v $(PYTHON_BOOTSTRAP) >/dev/null || { \
		echo -e "  $(RED)✗$(RESET) $(PYTHON_BOOTSTRAP) fehlt (PYTHON_BOOTSTRAP=… überschreibt)" >&2; exit 1; }
	@test -x $(PYTHON) || $(PYTHON_BOOTSTRAP) -m venv $(VENV)
	@$(PYTHON) -m pip install -q --disable-pip-version-check -e '.[dev]' || { \
		echo -e "  $(RED)✗$(RESET) Pakete nicht installiert: Netz und Paketindex prüfen" >&2; exit 1; }
	@touch "$@"
	@echo -e "  $(GREEN)✓$(RESET) .venv eingerichtet"

# Die .mo sind nicht im Git, damit parallele Tickets nicht an Binärdateien kollidieren.
%.mo: %.po $(VENV)/.installed
	@$(PYBABEL) --quiet compile -i "$<" -o "$@"
	@echo -e "  $(GREEN)✓$(RESET) Übersetzung $@ erzeugt"

# Ohne Hilfeeintrag: Prüf-Targets richten nichts ein, sie melden eine fehlende oder veraltete
# Einrichtung.
.PHONY: require-setup
require-setup:
	@$(MAKE) --no-print-directory -q $(SETUP_STAMPS) 2>/dev/null || { \
		echo -e "  $(RED)✗$(RESET) Nicht eingerichtet oder veraltet: $(YELLOW)make setup$(RESET)" >&2; \
		exit 1; }

# ─── Status ──────────────────────────────────────────────────────────────────

##@ Status

.PHONY: status
status: require-tools ## Git-Status des Repos (repo-status)
	@repo-status --show

# ─── Entwicklung ─────────────────────────────────────────────────────────────

##@ Entwicklung

# Voller Prüflauf, auch für agent-lessons (integration_check: make check).
.PHONY: check
check: require-setup lint test ## Voller Prüflauf: Lint, Formatprüfung, Doku-Prüfung und Tests

.PHONY: test
test: docs-check require-setup ## Doku-Prüfung und Tests  [ARGS="-k name"]
	@$(PYTHON) -m pytest -q $(ARGS)

.PHONY: docs-check
docs-check: require-tools ## Nutzerdoku gegen das Projekt prüfen (Links, Befehle, Variablen)
	@docs-check --run

.PHONY: lint
lint: require-setup ## Ruff (Lint und Format) und Shellcheck
	@$(RUFF) check -q src tests setup.py
	@$(RUFF) format -q --check src tests setup.py
	@shellcheck $(SHELL_FILES)
	@echo -e "  $(GREEN)✓$(RESET) Lint sauber"

.PHONY: format
format: require-setup ## Python-Dateien mit Ruff formatieren
	@$(RUFF) format src tests setup.py

# Zum Vergleich mit dem Katalog; die .po wird von Hand gepflegt (docs/development.md).
.PHONY: messages
messages: require-setup ## Alle Texte des Codes (_) nach build/mmit-devtools.pot sammeln
	@mkdir -p build
	@$(PYBABEL) --quiet extract -F babel.cfg --no-location -o build/mmit-devtools.pot .
	@echo -e "  $(GREEN)✓$(RESET) build/mmit-devtools.pot"

# ─── Versionierung ───────────────────────────────────────────────────────────

# Nach versioning-conventions: Die Version steht nur in pyproject.toml; lesen und erhöhen über
# BashLib (readProjectVersion, semVerBump).

##@ Versionierung

.PHONY: version
version: precheck ## Aktuelle Version anzeigen (Versionsdatei + git tag) — Maintainer
	@echo
	@VER=$$(source "$${BASH_LIBS}/version.lib.sh" 2>/dev/null && readProjectVersion 2>/dev/null); \
	 [[ -z "$$VER" ]] && VER='nicht gesetzt'; \
	 TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo 'kein Tag'); \
	 echo "    $(YELLOW)version$(RESET)      = $(BLUE)$$VER$(RESET)"; \
	 echo "    $(YELLOW)git tag$(RESET)      = $(BLUE)$$TAG$(RESET)"
	@echo

.PHONY: tags
tags: ## Letzte 10 Tags mit Message anzeigen
	@echo
	@git tag --sort=-version:refname -n1 | head -10 | \
	  awk '{printf "    $(BLUE)%-28s$(RESET) $(GREEN)%s$(RESET)\n", $$1, substr($$0, index($$0,$$2))}'
	@echo

.PHONY: changelog
changelog: require-tools ## Vorschau des Changelogs aus Tags und Commits
	@changelog --dry-run

# $(call release,major|minor|patch): bumpen, taggen, pushen, dann CHANGELOG.md
define release
	source "$${BASH_LIBS}/version.lib.sh" && semVerBump $(1) auto "" "$${MSG:-}"
	@changelog --publish
endef

# require-tools vor precheck: ohne ProjectTools bricht ein Release vor dem Bump ab, nicht erst
# nach dem gepushten Tag.
.PHONY: tag-major
tag-major: require-tools precheck ## Major-Release  [MSG="..."] — Maintainer
	$(call release,major)

.PHONY: tag-minor
tag-minor: require-tools precheck ## Minor-Release  [MSG="..."] — Maintainer
	$(call release,minor)

.PHONY: tag-patch
tag-patch: require-tools precheck ## Patch-Release  [MSG="..."] — Maintainer
	$(call release,patch)
