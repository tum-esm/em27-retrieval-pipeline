import datetime
from typing import Optional
import pytest
import src


@pytest.mark.em27_metadata_library
def test_explosion() -> None:
    locations = src.em27_metadata.types.LocationMetadataList(
        root=[
            src.em27_metadata.types.LocationMetadata(
                location_id="lid1",
                details="description of location 1",
                lon=10.5,
                lat=48.1,
                alt=500,
            ),
            src.em27_metadata.types.LocationMetadata(
                location_id="lid2",
                details="description of location 2",
                lon=11.3,
                lat=48.0,
                alt=600,
            ),
        ]
    )
    # fmt: off
    sensors = src.em27_metadata.types.SensorMetadataList(
        root=[
            src.em27_metadata.types.SensorMetadata(
                sensor_id="sid1",
                serial_number=51,
                setups=[
                    src.em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-01T01:00:00+0000",# pyright: ignore[reportArgumentType]
                        to_datetime="2020-02-01T09:59:59+0000",# pyright: ignore[reportArgumentType]
                        value=src.em27_metadata.types.Setup(
                            lid="lid1", pds="A", utc_offset=3.7, profile_lid="lid2" # pyright: ignore[reportCallIssue]
                        ),
                    ),
                    src.em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-01T12:00:00+0000",# pyright: ignore[reportArgumentType]
                        to_datetime="2020-02-01T21:59:59+0000",# pyright: ignore[reportArgumentType]
                        value=src.em27_metadata.types.Setup(lid="lid1", pds="B"),# pyright: ignore[reportCallIssue]
                    ),
                    src.em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-01T22:00:00+0000",# pyright: ignore[reportArgumentType]
                        to_datetime="2020-02-03T22:59:59+0000", # pyright: ignore[reportArgumentType]
                        value=src.em27_metadata.types.Setup(lid="lid1", pds="C"), # pyright: ignore[reportCallIssue]
                    ),
                    src.em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-04T00:00:00+0000",# pyright: ignore[reportArgumentType]
                        to_datetime="2020-02-04T20:59:59+0000",# pyright: ignore[reportArgumentType]
                        value=src.em27_metadata.types.Setup(lid="lid1", pds="D"),# pyright: ignore[reportCallIssue]
                    ),
                    src.em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-04T22:00:00+0000",# pyright: ignore[reportArgumentType]
                        to_datetime="2020-02-04T23:59:59+0000",# pyright: ignore[reportArgumentType]
                        value=src.em27_metadata.types.Setup(lid="lid1", pds="E"),# pyright: ignore[reportCallIssue]
                    ),
                ]
            ),
        ]
    )
    # fmt: on

    metadata = src.em27_metadata.interfaces.EM27MetadataInterface(
        locations,
        sensors,
        campaigns=src.em27_metadata.types.CampaignMetadataList(root=[]),
    )

    # fmt: off
    data: list[tuple[datetime.datetime, Optional[str]]] = [
        (datetime.datetime(2020, 2, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),   None),
        (datetime.datetime(2020, 2, 1, 0, 30, 0, tzinfo=datetime.timezone.utc),  None),
        (datetime.datetime(2020, 2, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),   "A"),
        (datetime.datetime(2020, 2, 1, 4, 0, 0, tzinfo=datetime.timezone.utc),   "A"),
        (datetime.datetime(2020, 2, 1, 9, 0, 0, tzinfo=datetime.timezone.utc),   "A"),
        (datetime.datetime(2020, 2, 1, 10, 0, 0, tzinfo=datetime.timezone.utc),  None),
        (datetime.datetime(2020, 2, 1, 11, 0, 0, tzinfo=datetime.timezone.utc),  None),
        (datetime.datetime(2020, 2, 1, 22, 30, 0, tzinfo=datetime.timezone.utc), "C"),
        (datetime.datetime(2020, 2, 1, 22, 45, 0, tzinfo=datetime.timezone.utc), "C"),
        (datetime.datetime(2020, 2, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),  "D"),
        (datetime.datetime(2020, 2, 4, 21, 0, 0, tzinfo=datetime.timezone.utc),  None),
        (datetime.datetime(2020, 2, 5, 20, 0, 0, tzinfo=datetime.timezone.utc),  None),
    ]
    # fmt: on

    result = metadata.explode_efficiently("sid1", [dt for dt, _ in data])
    print(result)
    for r, (_, expected) in zip(result, data):
        if r is None:
            assert expected is None
        else:
            location, _, pds, _ = r
            assert location.location_id == "lid1"
            assert pds == expected
