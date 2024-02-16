from json import loads
from pathlib import Path

import pytest

# Get relative path to samples dir no matter the working dir
sample_dir = Path(__file__).parent.resolve() / "samples"


@pytest.fixture
def sample_and_result(request):
    with open(sample_dir / f"{request.param[0]}.xml", encoding="utf-8") as sample:
        plain = len(request.param) > 1 and request.param[1]
        with open(sample_dir / f"{request.param[0]}{'_plain' if plain else ''}.json", encoding="utf-8") as result:
            return sample.read(), loads(result.read())
