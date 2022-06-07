from pathlib import Path

import pytest

# Get relative path to samples dir no matter the working dir
sample_dir = Path(__file__).parent.resolve() / "samples"


@pytest.fixture
def rss_version_2():
    with open(sample_dir / "rss_2.xml") as f:
        return f.read()


@pytest.fixture
def atom_feed():
    with open(sample_dir / "atom.xml") as f:
        return f.read()
