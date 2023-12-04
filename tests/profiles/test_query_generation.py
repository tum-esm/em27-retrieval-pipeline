from typing import Literal
import os
import tempfile
import pytest
import datetime
import em27_metadata
from src import profiles
from src.utils import utils
from tests.fixtures import provide_config_template


@pytest.mark.order(1)
@pytest.mark.ci_quick
@pytest.mark.ci_intensive
@pytest.mark.ci_complete
def test_query_generation(
    provide_config_template: utils.config.Config,
) -> None:
    config = provide_config_template
    assert config.profiles is not None

    em27_metadata_storage = em27_metadata.EM27MetadataInterface(
        locations=[
            em27_metadata.types.LocationMetadata(
                location_id="l1", details="l1d", lat=1, lon=2, alt=0
            ),
            em27_metadata.types.LocationMetadata(
                location_id="l2", details="l2d", lat=1, lon=3, alt=0
            ),
            em27_metadata.types.LocationMetadata(
                location_id="l3", details="l3d", lat=2, lon=3, alt=0
            ),
        ],
        sensors=[
            em27_metadata.types.SensorMetadata(
                sensor_id="s1",
                serial_number=1,
                locations=[
                    em27_metadata.types.SensorTypes.Location(
                        from_datetime="2000-01-01T00:00:00+00:00",
                        to_datetime="2000-03-01T11:59:59+00:00",
                        location_id="l1",
                    ),
                    em27_metadata.types.SensorTypes.Location(
                        from_datetime="2000-03-01T12:00:00+00:00",
                        to_datetime="2000-05-01T23:59:59+00:00",
                        location_id="l3",
                    ),
                    em27_metadata.types.SensorTypes.Location(
                        from_datetime="2000-05-04T12:00:00+00:00",
                        to_datetime="2000-05-07T23:59:59+00:00",
                        location_id="l2",
                    ),
                ],
            ),
            em27_metadata.types.SensorMetadata(
                sensor_id="s2",
                serial_number=2,
                locations=[
                    em27_metadata.types.SensorTypes.Location(
                        from_datetime="2000-01-07T00:00:00+00:00",
                        to_datetime="2000-02-23T23:59:59+00:00",
                        location_id="l1",
                    ),
                    em27_metadata.types.SensorTypes.Location(
                        from_datetime="2000-05-05T12:00:00+00:00",
                        to_datetime="2000-05-08T23:59:59+00:00",
                        location_id="l2",
                    ),
                ],
            ),
        ],
        campaigns=[],
    )

    versions: list[Literal["GGG2014", "GGG2020"]] = ["GGG2014", "GGG2020"]

    # create a "with tmp dir"
    with tempfile.TemporaryDirectory() as tmp_dir:
        config.general.data_src_dirs.profiles = tmp_dir
        config.profiles.request_scope.from_date = datetime.date(2000, 1, 1)
        config.profiles.request_scope.to_date = datetime.date(2000, 5, 30)

        for version in versions:
            os.mkdir(os.path.join(tmp_dir, version))
            query_list = profiles.generate_queries.generate_download_queries(
                config=config,
                version=version,
                em27_metadata_storage=em27_metadata_storage,
            )
            [print(q) for q in query_list]
            assert len(query_list) == 7

            def assert_query_exists(
                lat: int,
                lon: int,
                from_date: datetime.date,
                to_date: datetime.date,
            ) -> None:
                assert (
                    sum([
                        all([
                            (q.lat == lat),
                            (q.lon == lon),
                            (q.from_date == from_date),
                            (q.to_date == to_date),
                        ]) for q in query_list
                    ]) == 1
                )

            print(query_list)

            assert_query_exists(
                lat=1,
                lon=2,
                from_date=datetime.date(2000, 1, 1),
                to_date=datetime.date(2000, 1, 28),
            )
            assert_query_exists(
                lat=1,
                lon=2,
                from_date=datetime.date(2000, 1, 29),
                to_date=datetime.date(2000, 2, 25),
            )
            assert_query_exists(
                lat=1,
                lon=2,
                from_date=datetime.date(2000, 2, 26),
                to_date=datetime.date(2000, 3, 1),
            )
            assert_query_exists(
                lat=2,
                lon=3,
                from_date=datetime.date(2000, 3, 1),
                to_date=datetime.date(2000, 3, 28),
            )
            assert_query_exists(
                lat=2,
                lon=3,
                from_date=datetime.date(2000, 3, 29),
                to_date=datetime.date(2000, 4, 25),
            )
            assert_query_exists(
                lat=2,
                lon=3,
                from_date=datetime.date(2000, 4, 26),
                to_date=datetime.date(2000, 5, 1),
            )
            assert_query_exists(
                lat=1,
                lon=3,
                from_date=datetime.date(2000, 5, 4),
                to_date=datetime.date(2000, 5, 8),
            )
