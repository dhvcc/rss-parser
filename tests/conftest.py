import json
from pathlib import Path
from typing import Dict, Iterator, Tuple, Type

from rss_parser import AtomParser, BaseParser, PodcastParser, RDFParser, RSSParser

# Get relative path to samples dir no matter the working dir
SAMPLES_DIR = Path(__file__).parent.resolve() / "samples"

# Feeds captured from the wild, each with a hand-written expect.json - see tests/corpus/README.md
CORPUS_DIR = Path(__file__).parent.resolve() / "corpus"

# Samples are grouped by feed kind: tests/samples/<kind>/<name>/data.xml + result.json.
# Adding a new sample dir is enough for it to be picked up by the snapshot tests.
PARSERS_BY_KIND: Dict[str, Type[BaseParser]] = {
    "rss": RSSParser,
    "atom": AtomParser,
    "rdf": RDFParser,
    "podcast": PodcastParser,
}


def iter_samples() -> Iterator[Tuple[str, Path]]:
    """Yield (kind, sample_dir) for every sample that has a data.xml."""
    for kind_dir in sorted(SAMPLES_DIR.iterdir()):
        if not kind_dir.is_dir():
            continue
        for sample_dir in sorted(kind_dir.iterdir()):
            if (sample_dir / "data.xml").is_file():
                yield kind_dir.name, sample_dir


def iter_corpus() -> Iterator[Tuple[str, Path]]:
    """Yield (kind, feed_dir) for every corpus feed that has a data.xml."""
    for kind_dir in sorted(d for d in CORPUS_DIR.iterdir() if d.is_dir()):
        for feed_dir in sorted(kind_dir.iterdir()):
            if (feed_dir / "data.xml").is_file():
                yield kind_dir.name, feed_dir


def read_sample(sample_dir: Path) -> str:
    return (sample_dir / "data.xml").read_text(encoding="utf-8")


def read_snapshot(sample_dir: Path) -> dict:
    return json.loads((sample_dir / "result.json").read_text(encoding="utf-8"))


def dump_for_snapshot(model) -> dict:
    # mode="json" so that datetimes and other rich types compare as their JSON form
    return model.model_dump(mode="json", by_alias=True)
