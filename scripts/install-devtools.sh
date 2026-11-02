#!/usr/bin/env bash
# DevTools aus diesem Stand mit pipx auf den Rechner bringen, samt Extra theme (Farben, T-7).
# Aufruf über make install; Argument: der Python der .venv, der das Wheel baut.
#
# Das Wheel liegt im Cache des Nutzers, nicht im Checkout: pipx merkt sich die Datei als Quelle,
# und ein Worktree verschwindet nach dem Aufräumen. Gelöscht werden nur ältere DevTools-Wheels in
# diesem eigenen Cache-Ordner und der temporäre Bauordner.
set -euo pipefail

usage() {
    echo "Aufruf: $(basename "$0") PYTHON" >&2
    echo "  Baut DevTools als Wheel mit PYTHON und installiert es mit pipx samt Extra theme." >&2
}

# Cache-Ordner nach XDG; ein relativer XDG_CACHE_HOME gilt nach der Spezifikation nicht.
cache_dir() {
    local base="${XDG_CACHE_HOME:-}"
    [[ "$base" == /* ]] || base="$HOME/.cache"
    printf '%s/mmit-devtools' "$base"
}

# Temporärer Bauordner; global, weil der EXIT-Trap erst nach main läuft.
build=""

main() {
    if [[ $# -ne 1 ]]; then
        usage
        exit 2
    fi
    local python="$1" cache wheel
    if ! command -v pipx >/dev/null; then
        echo "  ✗ pipx fehlt; etwa mit brew install pipx (https://pipx.pypa.io)" >&2
        exit 1
    fi
    build="$(mktemp -d)"
    trap 'rm -rf "${build}"' EXIT
    if ! "$python" -m pip wheel -q --disable-pip-version-check --no-deps -w "$build" .; then
        echo "  ✗ Wheel nicht gebaut: Netz und Paketindex prüfen" >&2
        exit 1
    fi
    cache="$(cache_dir)"
    mkdir -p "$cache"
    rm -f "$cache"/mmit_devtools-*.whl
    mv "$build"/mmit_devtools-*.whl "$cache"/
    wheel="$(ls "$cache"/mmit_devtools-*.whl)"
    # name[extra] @ file://…: Nur so installiert pipx das Extra mit; „datei.whl[theme]“ übergeht es.
    pipx install --force --quiet "mmit-devtools[theme] @ file://$wheel"
    echo "  ✓ $("$(pipx environment --value PIPX_BIN_DIR)/devtools" --version) installiert (pipx)"
}

main "$@"
