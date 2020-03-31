from pathlib import Path

import pytest


@pytest.fixture
def data_path() -> Path:
  return Path(__file__).parent / "testdata"

@pytest.fixture
def dummy_config_path(data_path: Path) -> Path:
    return data_path / "experiment_configs/dummy.yml"