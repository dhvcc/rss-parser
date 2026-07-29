import pytest

from tests.conftest import (
    PARSERS_BY_KIND,
    dump_for_snapshot,
    iter_samples,
    read_sample,
    read_snapshot,
)

SAMPLES = list(iter_samples())


@pytest.mark.parametrize(
    ("kind", "sample_dir"),
    SAMPLES,
    ids=[f"{kind}/{sample_dir.name}" for kind, sample_dir in SAMPLES],
)
def test_sample_matches_snapshot(kind, sample_dir):
    """Every sample must parse and produce exactly the committed result.json.

    To update snapshots intentionally: python -m scripts.update_snapshots
    """
    parser = PARSERS_BY_KIND[kind]

    parsed = parser.parse(read_sample(sample_dir))

    assert parsed
    assert dump_for_snapshot(parsed) == read_snapshot(sample_dir)
