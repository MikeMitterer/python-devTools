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
export WORKSPACE WORKSPACE_SQ PROJECT_NAME

# Release-Tags der pipx-Werkzeuge stehen in .dev-tools.conf.sh; selbst entwickelt: make hints.
include .dev-tools.conf.sh
PROJECTTOOLS_MIN     := $(patsubst v%,%,$(firstword $(subst +, ,$(PROJECTTOOLS_TAG))))
PROJECTTOOLS_INSTALL := pipx install --force 'git+https://github.com/MikeMitterer/bash-ProjectTools.git@$(PROJECTTOOLS_TAG)'
PROJECTTOOLS_FOUND    = $(shell projecttools --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)

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
THEME_INDENT_GROUP  ?= $(shell printf '%2s' '')
THEME_INDENT_TARGET ?= $(shell printf '%7s' '')
THEME_WIDTH_TARGET  ?= 22
THEME_COLUMN_GAP    ?= 1

# Hooks dieses Repos; setup trägt sie ein, require-setup prüft das.
HOOKS_PATH  := .githooks
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
	    { printf "$(THEME_INDENT_TARGET)$(THEME_COLOR_TARGET)%-$(THEME_WIDTH_TARGET)s%$(THEME_COLUMN_GAP)s$(THEME_COLOR_DESC)%s$(RESET)\n", $$1, "", $$2 }'
	@echo

.PHONY: info
info: ## Umgebung, Pfade und Werkzeugversionen anzeigen
	@echo
	@printf "    $(YELLOW)%-16s$(RESET) = $(BLUE)%s$(RESET)\n" \
		PROJECT_NAME "$${PROJECT_NAME}" \
		WORKSPACE "$${WORKSPACE}" \
		ProjectTools '$(or $(PROJECTTOOLS_FOUND),fehlt) (verlangt ab $(PROJECTTOOLS_MIN))' \
		DEV_MAKE "$${DEV_MAKE:-nicht gesetzt}"
	@echo

# Repo-Adresse aus git remote origin (SSH oder HTTPS) als https-URL. Sie kommt von außen und
# landet im Rezept; deshalb gilt sie nur aus erlaubten Zeichen, sonst leer.
REPO_URL  := $(shell git remote get-url origin 2>/dev/null | sed -E 's|^git@([^:]+):|https://\1/|; s|\.git$$||' | grep -xE '[A-Za-z0-9._:/@+~-]+')
NO_REMOTE := kein Remote origin (git remote add origin …)

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
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Werkzeuge$(RESET)"
	@$(call hint_row,ProjectTools ab $(PROJECTTOOLS_MIN),$(PROJECTTOOLS_INSTALL))
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Werkzeuge selbst entwickeln$(RESET)"
	@$(call tool_checkout,PROJECT_TOOLS,mmit-projecttools); $(call hint_row,ProjectTools,$$checkout)
	@echo
	@echo "$(THEME_INDENT_GROUP)$(THEME_COLOR_GROUP)Links$(RESET)"
	@$(call hint_row,Repository,$(or $(REPO_URL),$(NO_REMOTE)))
	@echo

# ─── Precheck ────────────────────────────────────────────────────────────────

# Ohne Hilfeeintrag: verlangt ProjectTools in Mindestversion und nennt sonst den Installationsbefehl.
.PHONY: require-tools
require-tools:
	@found='$(PROJECTTOOLS_FOUND)'; \
	if [[ -z "$$found" ]]; then problem='fehlt'; \
	elif [[ "$$(printf '%s\n' '$(PROJECTTOOLS_MIN)' "$$found" | sort -V | head -1)" != '$(PROJECTTOOLS_MIN)' ]]; then problem="$$found ist zu alt"; \
	else exit 0; fi; \
	printf '  $(RED)✗$(RESET) ProjectTools %s (verlangt ab %s): $(YELLOW)%s$(RESET)\n' "$$problem" '$(PROJECTTOOLS_MIN)' "$(PROJECTTOOLS_INSTALL)" >&2; \
	exit 1

# ─── Setup ───────────────────────────────────────────────────────────────────

##@ Setup

# Der einzige Einrichtungsweg, auch für agent-lessons (worktree_setup). Wiederholbar und ohne
# Rückfrage; heute trägt er nur die Git-Hooks ein.
.PHONY: setup
setup: ## Git-Hooks einrichten (pre-commit: make docs-check)
	@git config core.hooksPath $(HOOKS_PATH)
	@echo -e "  $(GREEN)✓$(RESET) Git-Hooks aus $(HOOKS_PATH)"

# Ohne Hilfeeintrag: Prüf-Targets richten nichts ein, sie melden eine fehlende Einrichtung.
.PHONY: require-setup
require-setup:
	@[[ "$$(git config --get core.hooksPath)" == '$(HOOKS_PATH)' ]] || { \
		echo -e "  $(RED)✗$(RESET) Nicht eingerichtet: $(YELLOW)make setup$(RESET)" >&2; \
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
check: require-setup lint docs-check ## Voller Prüflauf: Shellcheck und Doku-Prüfung

.PHONY: docs-check
docs-check: require-tools ## Nutzerdoku gegen das Projekt prüfen (Links, Befehle, Variablen)
	@docs-check --run

.PHONY: lint
lint: ## Shellcheck für Hook und Configs
	@shellcheck $(SHELL_FILES)
	@echo -e "  $(GREEN)✓$(RESET) Lint sauber"
