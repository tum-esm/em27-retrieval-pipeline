from typing import Any
import os
import random
import tempfile
import pytest
import src
from ..fixtures import provide_config_template
from .utils import generate_random_locations, generate_random_dates


@pytest.mark.order(3)
@pytest.mark.quick
def test_list_downloaded_data(
    provide_config_template: src.types.Config
) -> None:
    random_locations = generate_random_locations(n=30)
    random_dates = generate_random_dates(n=2000)
    cs = {
        l: src.utils.text.get_coordinates_slug(l.lat, l.lon)
        for l in random_locations
    }
    config = provide_config_template.model_copy(deep=True)
    assert config.profiles is not None
    config.profiles.scope.from_date = min(random_dates)
    config.profiles.scope.to_date = max(random_dates)
    for _ in range(5):
        downloaded_data = {
            l: set(random.sample(random_dates, 30))
            for l in random.sample(random_locations, 5)
        }
        model_filenames: dict[Any, list[str]] = {
            "GGG2014": [
                f"{d.strftime('%Y%m%d')}_{cs[l]}.{e}" for e in ["map", "mod"]
                for l in downloaded_data.keys() for d in downloaded_data[l]
            ],
            "GGG2020": [
                f"{d.strftime('%Y%m%d')}{h:02d}_{cs[l]}.{e}"
                for e in ["map", "mod", "vmr"] for l in downloaded_data.keys()
                for d in downloaded_data[l] for h in range(0, 24, 3)
            ],
        }
        for model, filenames in model_filenames.items():
            with tempfile.TemporaryDirectory() as tmpdir:
                config.general.data.atmospheric_profiles.root = tmpdir
                os.mkdir(os.path.join(tmpdir, model))
                for filename in filenames:
                    with open(os.path.join(tmpdir, model, filename), "w"):
                        pass
                downloaded = src.profiles.generate_queries.list_downloaded_data(
                    config, model
                )
                assert downloaded.keys() == downloaded_data.keys()
                for l in downloaded_data.keys():
                    assert downloaded[l] == downloaded_data[l]
