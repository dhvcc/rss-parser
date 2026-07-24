"""
Regenerate tests/samples/**/result.json snapshots from data.xml files.

Run from the repo root after intentionally changing model output:

    python -m scripts.update_snapshots
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import PARSERS_BY_KIND, dump_for_snapshot, iter_samples, read_sample


def main() -> None:
    for kind, sample_dir in iter_samples():
        parser = PARSERS_BY_KIND[kind]
        parsed = parser.parse(read_sample(sample_dir))
        snapshot = dump_for_snapshot(parsed)
        (sample_dir / "result.json").write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        sys.stdout.write(f"updated {sample_dir.relative_to(sample_dir.parent.parent.parent)}\n")


if __name__ == "__main__":
    main()
