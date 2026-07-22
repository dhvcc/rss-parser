# Contributing

Pull requests are welcome. For major changes, please open an
[issue](https://github.com/dhvcc/rss-parser/issues) first to discuss what you would like to change.

## Setup

```bash
pip install poetry
poetry install
```

Using `pre-commit` is highly recommended. To install hooks, run:

```bash
poetry run pre-commit install -t=pre-commit -t=pre-push
```

## Running checks

```bash
poetry run pytest --doctest-modules rss_parser tests
poetry run black --check .
poetry run ruff check .
poetry run mypy rss_parser
```

## Sample-based snapshot tests

Feed samples live in `tests/samples/<kind>/<name>/` where `<kind>` is one of
`rss`, `atom`, `rdf`, `podcast`. Each sample dir contains:

- `data.xml` — the feed
- `result.json` — the expected `model_dump` output

Dropping a new sample directory in is enough — the snapshot test discovers it automatically.
To (re)generate `result.json` after adding a sample or intentionally changing model output:

```bash
poetry run python -m scripts.update_snapshots
```

Review the resulting diff carefully — the snapshots are the contract.

## Docs

Docs are built with [mkdocs-material](https://squidfunk.github.io/mkdocs-material/):

```bash
poetry install --with docs
poetry run mkdocs serve
```
