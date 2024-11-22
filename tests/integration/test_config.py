import pytest

import src

@pytest.mark.order(2)
@pytest.mark.integration
def test_config() -> None:
    src.types.Config.load()
