# Changelog

Generated from release tags and Conventional Commits.

## v0.3.0+261102.1831.3723d — 2026-11-02

devtools upgrade (neueste Release-Tags, -n, --write, gepinnte Tags), Farben und Leerzeile am Ende über CLITheme (Extra theme), make install, Python 3.14

### Features

- devtools upgrade holt den neuesten Release-Tag je Quelle (T-5) (`4bfcaf5`)
- upgrade aktualisiert auch gepinnte Tags und nennt jeden NAME\_TAG (T-6) (`3d148fe`)
- Ausgabe in den Farben von CLITheme, optional über das Extra theme (T-7) (`c295e3b`)
- make install bringt DevTools aus diesem Stand mit pipx auf den Rechner (T-9) (`476c7b7`)
- Jede Ausgabe endet mit einer Leerzeile, über den Abschluss von CLITheme (T-10) (`75c5647`)

### Fixes

- upgrade --write schreibt nur Tags, die die Installation erreicht (T-5, R1-F1, R1-F2) (`df611dd`)
- Ausgabe im Terminal nicht umbrechen, nur färben (T-7, R1-F1) (`6c81dd2`)
- make install installiert das Extra theme und hängt nicht am Worktree (T-9, R1-F1, R1-F2) (`1fdd6c3`)
- Config-Fehler mit Beispiel enden mit genau einer Leerzeile (T-10, R1-F1) (`7129078`)

### Other changes

- Mindestversion Python 3.14, Typparameter statt TypeVar (T-8) (`3f84648`)
- emit schreibt über Output.write(wrap=False) von CLITheme 0.4.0 (T-11) (`b75e547`)

## v0.2.0+261101.1319.09840 — 2026-11-01

Erstes Release: devtools prüft, zeigt und installiert die pipx-Werkzeuge aus .dev-tools.conf.sh, englisch und deutsch, unter der EUPL 1.2

### Features

- Entwicklungswerkzeuge aus .dev-tools.conf.sh mit devtools prüfen, zeigen und installieren (T-2) (`c8d03c1`)
- devtools englisch als Basis, deutsch aus dem Katalog (T-2) (`7cd82fc`)

### Fixes

- Kataloge und Tests auch in einem Checkout-Pfad mit $(…) (T-2) (`9081874`)
- Paket von PyPI nicht als Arbeitskopie werten (T-2, R1-F1) (`3cb14ba`)
- precheck prüft die BashLib-Version auch bei BASH\_LIBS von außen (T-4, R1-F1) (`6ef622f`)

### Documentation

- DevTools unter der EUPL 1.2 mit MangoLila GmbH als Lizenzgeberin (T-3) (`df8b269`)
