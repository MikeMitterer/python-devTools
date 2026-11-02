<div align="center">

# DevTools

**Check, show and install the development tools of a project with pipx**

[Example](#example) · [Quick start](#quick-start) · [Config file](#config-file) · [Commands](#commands) · [Development](docs/development.md)

English · [Deutsch](README.de.md)

</div>

DevTools reads the development tools a project needs from its
`.dev-tools.conf.sh`: for each tool the pipx package, the release tag and the
source, either a Git URL or a local working copy. The command `devtools`
shows what is installed, brings every tool to its source and tag with pipx
and checks the minimum version, the same way in every project instead of in
each Makefile.

## Contents

- [Example](#example)
- [Features](#features)
- [Quick start](#quick-start)
- [Config file](#config-file)
- [Commands](#commands)
- [Development](#development)
- [License](#license)

## Example

```console
$ devtools install
  ProjectTools  current (0.3.2)
  BashLib       updated from 0.1.0 to 0.2.0 (git+https://github.com/MikeMitterer/bash-lib.git)
```

One line per tool: current, updated from one version to another, installed,
or a working copy. The output is in English or German, depending on the
locale (`LANGUAGE`, `LC_ALL`, `LANG`).

[↑ Contents](#contents)

## Features

- **One config file:** tools, pipx packages, tags and sources in
  `.dev-tools.conf.sh`, readable by Make and Bash as well.
- **Git or working copy:** a tool comes from a Git URL at the tag, or from a
  local checkout, editable (`pipx install -e`) or as a fixed copy.
- **Working copies stay:** if you installed a working copy yourself while the
  config asks for Git, `devtools install` leaves it alone and says so.
- **Correct version of a working copy:** pipx freezes the package version of
  an editable install; DevTools reads the version from the working copy's
  `pyproject.toml` instead.
- **Upgrade to the newest release:** `devtools upgrade` finds the newest
  release tag of each source, from the Git remote or the working copy's
  repository, and installs it; `-n` shows installed, config and newest
  version side by side, `--write` puts the newer tags into the config.
- **Minimum version check:** `devtools check NAME` fails with the install
  command, ready for a Makefile.
- **Standard library only:** Python 3.14 or later, no further packages at
  runtime.

[↑ Contents](#contents)

## Quick start

Requirements: Python 3.14 or later and [pipx](https://pipx.pypa.io/).

Tags follow the scheme `vX.Y.Z+YYMMDD.HHMM.hash`, and pipx needs the full
tag. This command shows the latest one:

```bash
git ls-remote --tags --refs --sort=-v:refname https://github.com/MikeMitterer/python-devtools.git | head -1
```

**Without installing:** run DevTools directly from Git in the project folder,
replacing `<release-tag>` with the tag:

```bash
pipx run --spec 'git+https://github.com/MikeMitterer/python-devtools.git@<release-tag>' devtools status
```

**Installed:** install it once, then use `devtools` in every project.

```bash
pipx install 'git+https://github.com/MikeMitterer/python-devtools.git@<release-tag>'
devtools install
```

[↑ Contents](#contents)

## Config file

`devtools` reads `.dev-tools.conf.sh` in the current folder; `--config`
names another file. Each line is `NAME=value` without quotes and without
spaces around `=`, so that Make can include the file and Bash can source it.
`#` starts a comment. Every `NAME_PACKAGE` makes `NAME` a tool; the other
entries use the same prefix.

```bash
PROJECTTOOLS_PACKAGE=mmit-projecttools
PROJECTTOOLS_LABEL=ProjectTools
PROJECTTOOLS_TAG=v0.3.2+261029.1600.c7bbd
PROJECTTOOLS_SOURCE=git+https://github.com/MikeMitterer/bash-ProjectTools.git
PROJECTTOOLS_EDITABLE=yes
```

| Entry | Required | Meaning |
|---|---|---|
| `NAME_PACKAGE` | yes | pipx package of the tool, for example `mmit-projecttools` |
| `NAME_TAG` | yes | Release tag; its `X.Y.Z` part is the minimum version |
| `NAME_SOURCE` | yes | Git URL (installed at the tag) or path of a working copy, relative to the config file |
| `NAME_EDITABLE` | no | For a working copy: `yes` installs it editable (`pipx install -e`), `no` as a fixed copy; default `yes` |
| `NAME_LABEL` | no | Name in the output; default the package name |

**Pinned tag:** `NAME_TAG` and `NAME_SOURCE` without `NAME_PACKAGE` pin a tag
that DevTools does not install, for example the version a Makefile starts
with `pipx run`. `devtools upgrade` shows its newest tag and writes it with
`--write`; the other commands ignore it. Without `NAME_SOURCE` the newest tag
cannot be found.

```bash
DEVTOOLS_TAG=v0.2.0+261101.1319.09840
DEVTOOLS_SOURCE=git+https://github.com/MikeMitterer/python-devtools.git
```

[↑ Contents](#contents)

## Commands

| Command | Does |
|---|---|
| `devtools status` | Shows each tool's state and what `install` would do; installs nothing |
| `devtools install` | Installs missing or older tools from source and tag (`pipx install --force`) |
| `devtools upgrade [NAME]` | Installs the newest release tag of each source; `-n` (`--dry-run`) only shows installed, config and newest version, `--write` also writes the newer tags into the config |
| `devtools check NAME` | Exit 0 if the installed version reaches the tag's version, otherwise exit 1 with the install command |
| `devtools command NAME` | Prints the install command for the tool |

`NAME` is the prefix of the entries in lower case, for example
`projecttools`. `devtools --help` shows all options.

`upgrade` takes release tags of the form `vX.Y.Z`, optionally with a build
part such as `+261031.2038.b22f0`; other tags and pre-releases do not count.
For a Git source it asks the remote (`git ls-remote`), for a working copy the
tags of its repository; it never pulls or changes the working copy, and
without a readable tag it simply keeps the config's tag. An
editable working copy is live already, so there is nothing to install. If a
source cannot be read, the line says why, the other tools still run, and
`upgrade` exits with 1.

With `--write`, `upgrade` puts the newer tags into the config and names each
`NAME_TAG`: old → new, current, or why it stays. It only writes a tool's tag
that the installed version reaches afterwards, otherwise `devtools check`
would fail. Without `--write` the config stays as it is; the output then says
that it still names older tags. A `NAME_TAG` without `NAME_SOURCE` gets a
line of its own, because its newest tag is unknown. If the config lists
DevTools itself, it comes last, because pipx replaces the environment it runs
from.

[↑ Contents](#contents)

## Development

Setting up from the checkout, tests and releases are described in the
[developer documentation](docs/development.md) (German).

[↑ Contents](#contents)

## License

Copyright © 2026 Michael Mitterer. **MangoLila GmbH** is the provider and
licensor.

DevTools is licensed under the **[EUPL 1.2](LICENSE)**, version 1.2 only.
It permits personal and commercial use, changes, redistribution, sale and
hosting without a paid license.

If you redistribute DevTools or a changed version, or offer it as a network
service, keep the copyright and license notices, mark your changes and
provide the corresponding source under the license's copyleft rules.

The warranty and liability exclusions in EUPL Articles 7 and 8 also apply to
consumers, as far as the law permits. Mandatory rights remain unaffected,
including liability for intent, gross negligence, personal injury and product
liability. No additional guarantee is given.

Contact: **office@MangoLila.at**.

Details: [LICENSE](LICENSE) · [German license text](LICENSE.de.txt) ·
[Provider and consumer declaration](LICENSING.md)

[↑ Contents](#contents)
