.PHONY: run lint format unit coverage tests full-test check-requirements lock clean

run:
	uv run python bot.py

lint:
	uv run ruff check bot.py lib/
	uv run ruff format --check bot.py lib/
	uv run mypy bot.py lib/

format:
	uv run ruff check --fix bot.py lib/
	uv run ruff format bot.py lib/

unit:
	uv run coverage run --branch --source=./lib -m unittest discover -p '*utest.py' || test $$? -eq 5

coverage:
	uv run coverage report -m

tests: unit coverage

check-requirements:
	@uv export --no-dev --no-header --format requirements-txt --quiet 2>/dev/null | diff -q - requirements.txt > /dev/null 2>&1 \
		|| (printf "ERROR: requirements.txt is out of sync with uv.lock. Run 'make lock' to fix.\n" && exit 1)

lock:
	uv lock
	uv export --no-dev --no-header --format requirements-txt -o requirements.txt

full-test: check-requirements lint tests
	@printf "\nSuccess!\n"

clean:
	find . \( -path ./.venv -o -path ./.mypy_cache \) -prune -o \( -name __pycache__ -o -name .coverage \) -exec rm -rfv {} +
