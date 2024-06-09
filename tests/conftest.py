import pickle
from pathlib import Path

import pytest

# Get relative path to samples dir no matter the working dir
sample_dir = Path(__file__).parent.resolve() / "samples"


@pytest.fixture
def sample_and_result(request):
    sample_name = request.param[0]

    with open(sample_dir / sample_name / "data.xml", encoding="utf-8") as sample_file:
        sample = sample_file.read()

    with open(sample_dir / sample_name / "result.pkl", "rb") as result_file:
        result = pickle.load(result_file)

    return sample, result
