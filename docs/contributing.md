# Contributing

Pull requests are welcome. For major changes, please open an
[issue](https://github.com/dhvcc/rss-parser/issues) first to discuss what you would like to change.

## Setup

The project uses [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
uv sync
```

Using `pre-commit` is highly recommended. To install hooks, run:

```bash
uv run pre-commit install -t=pre-commit -t=pre-push
```

## Running checks

```bash
uv run pytest --doctest-modules rss_parser tests
uv run black --check .
uv run ruff check .
uv run mypy rss_parser
```

## Sample-based snapshot tests

Feed samples live in `tests/samples/<kind>/<name>/` where `<kind>` is one of
`rss`, `atom`, `rdf`, `podcast`. Each sample dir contains:

- `data.xml` — the feed
- `result.json` — the expected `model_dump` output

Dropping a new sample directory in is enough — the snapshot test discovers it automatically.
To (re)generate `result.json` after adding a sample or intentionally changing model output:

```bash
uv run python -m scripts.update_snapshots
```

Review the resulting diff carefully — the snapshots are the contract.

## Docs

Docs are built with [mkdocs-material](https://squidfunk.github.io/mkdocs-material/):

```bash
uv sync --group docs
uv run mkdocs serve
```
