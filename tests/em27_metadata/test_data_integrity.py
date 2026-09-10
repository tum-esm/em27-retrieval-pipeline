import datetime
import os
import pytest
import src

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# @pytest.mark.action
# def test_local_data_integrity() -> None:
#     src.em27_metadata.load_from_local_files(
#         locations_path=os.path.join(_PROJECT_DIR, "data", "locations.json"),
#         sensors_path=os.path.join(_PROJECT_DIR, "data", "sensors.json"),
#         campaigns_path=os.path.join(_PROJECT_DIR, "data", "campaigns.json"),
#     )


@pytest.mark.em27_metadata_library
def test_sample_data_integrity() -> None:
    for variant in ["toml", "json", "fallbacktest1", "fallbacktest2"]:
        location_data = src.em27_metadata.load_from_example_data(variant=variant)  # type: ignore
    example_sensor_data_contexts_1 = location_data.get(
        sensor_id="sid1",
        from_datetime=datetime.datetime(2020, 8, 26, 0, 0, 0, tzinfo=datetime.timezone.utc),
        to_datetime=datetime.datetime(2020, 8, 26, 23, 59, 59, tzinfo=datetime.timezone.utc),
    )
    assert len(example_sensor_data_contexts_1) == 1
    # example_list_str = (
    #    json.dumps(
    #        [example_sensor_data_contexts_1[0].model_dump()],
    #        indent=2,
    #    )
    #    .replace("\n", "")
    #    .replace("\t", "")
    #    .replace(" ", "")
    # )
    # with open(os.path.join(_PROJECT_DIR, "README.md")) as f:
    #    assert example_list_str in f.read().replace("\n", "").replace("\t", "").replace(" ", "")
