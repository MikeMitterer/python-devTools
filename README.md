# DevTools

The package `mmit-devtools` will check, show and install the development
tools a project lists in `.dev-tools.conf.sh`. It is not written yet; so far
the repository only holds its development setup.

## Development

```bash
make setup   # set up a fresh checkout (Git hooks); safe to run again
make check   # full check: shellcheck and docs-check
```

`make check` needs ProjectTools installed with pipx; `make hints` shows the
command and the order for a first start.
