.PHONY: install test lint typecheck check demo clean

install:
	poetry install
	cd remotion && npm install

test:
	poetry run pytest

lint:
	poetry run ruff check .

typecheck:
	poetry run mypy src

check: lint typecheck test

demo:
	poetry run repodcast build examples/sample-project --title "Sample Project" --minutes 1 --out dist/sample-project.mp4 --fake-ai --fake-audio

clean:
	rm -rf dist build .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache *.egg-info src/*.egg-info
