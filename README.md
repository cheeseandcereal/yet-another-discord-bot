# Yet Another Discord Bot

Yet another dumb discord bot

## Install/Dependencies

Requires Python 3.14+.

Clone the repo to get the code.

This project uses [uv](https://docs.astral.sh/uv/) for dependency
management. With uv installed, sync the environment:

    uv sync --no-dev          # runtime dependencies only
    uv sync                   # also install dev tools (ruff, mypy, coverage)

Without uv, `requirements.txt` is kept in sync with the lockfile and can
be installed with pip:

    python3 -m pip install -r requirements.txt --user

## Usage

To run with a one-time use token:

`uv run python bot.py -t <token>`

To save your token to the config file:

`uv run python bot.py -s <token>`

To run the bot with the saved token from the config file:

`uv run python bot.py` (or `make run`)

Display Help:

`uv run python bot.py --help`

## Development

Common tasks are exposed via the `Makefile`:

    make lint          # ruff check + format check + mypy
    make format        # auto-fix lint issues and reformat
    make tests         # unit tests + coverage report
    make full-test     # check-requirements + lint + tests
    make lock          # refresh uv.lock and regenerate requirements.txt
    make clean         # remove caches and coverage artifacts

After changing dependencies in `pyproject.toml`, run `make lock` to
update both `uv.lock` and `requirements.txt`. The `check-requirements`
target (run as part of `full-test`) verifies they stay in sync.
