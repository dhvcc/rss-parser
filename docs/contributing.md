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

## Test architecture

The suite is layered; each layer catches what the others can't:

1. **Spec tests** (`test_spec_compliance.py`, `test_spec_atom.py`, `test_tag.py`, `test_dates.py`,
   `test_detection.py`, `test_extensibility.py`, `test_itunes.py`, `test_errors.py`,
   `test_serialization.py`) — targeted assertions with hand-written expected values.
   This is where correctness lives.
2. **Property-based tests** (`test_properties.py`, [hypothesis](https://hypothesis.readthedocs.io)) —
   invariants that must hold for *generated* feeds: text round-trips, lists are always lists,
   unknown tags are never dropped, `model_validate(model_dump())` is idempotent.
3. **Real-world corpus** (`test_corpus.py`, `tests/corpus/`) — feeds captured from the wild
   (BBC, NPR, YouTube, Slashdot, GitHub, podcasts...), parsed offline. Expectations in each
   `expect.json` are derived by *reading the raw XML*, never by running the parser —
   see `tests/corpus/README.md`.
4. **Serialization snapshots** (`test_snapshots.py`, `tests/samples/`) — full `model_dump`
   contracts for small curated samples, guarding the output shape against accidental changes.
   Regenerate after intentional changes with:

    ```bash
    uv run python -m scripts.update_snapshots
    ```

    Review the resulting diff carefully — the snapshots are the contract.

Coverage has a CI-enforced floor (`fail_under` in `pyproject.toml`).

Both samples and corpus feeds are discovered automatically — dropping a new directory in
is enough.

## Docs

Docs are built with [mkdocs-material](https://squidfunk.github.io/mkdocs-material/):

```bash
uv sync --group docs
uv run mkdocs serve
```
