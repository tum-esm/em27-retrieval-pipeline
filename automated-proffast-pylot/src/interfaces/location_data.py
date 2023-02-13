from datetime import datetime, timedelta
import json
from typing import Any, Optional, Union
import requests
from src import custom_types


class LocationDataInterface:
    def __init__(
        self,
        version: str,
        locations: list[Any],
        sensors: list[Any],
        campaigns: list[Any],
    ):
        self.version = version

        self.locations: list[custom_types.Location] = [
            custom_types.Location(**l) for l in locations
        ]
        self.location_ids = [s.location_id for s in self.locations]

        self.sensors: list[custom_types.Sensor] = [
            custom_types.Sensor(**s) for s in sensors
        ]
        self.sensor_ids = [s.sensor_id for s in self.sensors]

        self.campaigns: list[custom_types.Campaign] = [
            custom_types.Campaign(**c) for c in campaigns
        ]
        self.campaign_ids = [s.campaign_id for s in self.campaigns]

        self.check_integrity()

    def check_integrity(self) -> None:
        # unique location ids
        assert len(set(self.location_ids)) == len(
            self.location_ids
        ), "location ids are not unique"

        # unique sensor ids
        assert len(set(self.sensor_ids)) == len(
            self.sensor_ids
        ), "sensor ids are not unique"

        # unique campaign ids
        assert len(set(self.campaign_ids)) == len(
            self.campaign_ids
        ), "campaign ids are not unique"

        # reference existence in sensors.json
        for s in self.sensors:
            for l in s.locations:
                assert (
                    l.location_id in self.location_ids
                ), f"unknown location id {l.location_id}"

        # reference existence in campaigns.json
        for c in self.campaigns:
            for s2 in c.stations:
                assert (
                    s2.default_location_id in self.location_ids
                ), f"unknown location id {s2.default_location_id}"
                assert (
                    s2.sensor_id in self.sensor_ids
                ), f"unknown sensor id {s2.sensor_id}"

        # integrity of time series in sensors.json
        for s in self.sensors:
            xss: list[
                Union[
                    list[custom_types.SensorUTCOffset],
                    list[custom_types.SensorPressureCalibrationFactor],
                    list[custom_types.SensorLocation],
                ]
            ] = [s.utc_offsets, s.pressure_calibration_factors, s.locations]
            for xs in xss:
                for x in xs:
                    assert x.from_date <= x.to_date, (
                        "from_date has to smaller than to_date "
                        + f"({x.from_date} > {x.to_date})"
                    )
                for i in range(len(xs) - 1):
                    x1, x2 = xs[i : i + 2]
                    expected_x2_from_date = (
                        datetime.strptime(x1.to_date, "%Y%m%d") + timedelta(days=1)
                    ).strftime("%Y%m%d")
                    assert not (
                        expected_x2_from_date > x2.from_date
                    ), f"time periods are overlapping: {x1.dict()}, {x1.dict()}"
                    assert not (
                        expected_x2_from_date < x2.from_date
                    ), f"time periods have gaps: {x1.dict()}, {x1.dict()}"

            for o1, o2 in zip(s.utc_offsets[:-1], s.utc_offsets[1:]):
                assert (
                    o1.utc_offset != o2.utc_offset
                ), "two neighboring date ranges should not have the same utc_offset"

            for p1, p2 in zip(
                s.pressure_calibration_factors[:-1], s.pressure_calibration_factors[1:]
            ):
                assert (
                    p1.factor != p2.factor
                ), "two neighboring date ranges should not have the same pressure calibration factor"

            for l1, l2 in zip(s.locations[:-1], s.locations[1:]):
                assert (
                    l1.location_id != l2.location_id
                ), "two neighboring date ranges should not have the same location_id"

    def get_sensor_data_context(
        self, sensor_id: str, date: str
    ) -> custom_types.SensorDataContext:
        # get the sensor
        assert (
            sensor_id in self.sensor_ids
        ), f'No location data for sensor_id "{sensor_id}"'
        sensor = list(filter(lambda s: s.sensor_id == sensor_id, self.sensors))[0]

        # get utc offset at that date
        utc_offset_matches = list(
            filter(lambda o: o.from_date <= date <= o.to_date, sensor.utc_offsets)
        )
        assert (
            len(utc_offset_matches) == 1
        ), f"no utc offset data for {sensor_id}/{date}"
        utc_offset = utc_offset_matches[0].utc_offset

        # get pressure calibration factor at that date
        pressure_calibration_factor_matches = list(
            filter(
                lambda o: o.from_date <= date <= o.to_date,
                sensor.pressure_calibration_factors,
            )
        )
        assert (
            len(pressure_calibration_factor_matches) == 1
        ), f"no pressure calibration data for {sensor_id}/{date}"
        pressure_calibration_factor = pressure_calibration_factor_matches[0].factor

        # get location at that date
        location_matches = list(
            filter(lambda l: l.from_date <= date <= l.to_date, sensor.locations)
        )
        assert len(location_matches) == 1, f"no location data for {sensor_id}/{date}"
        location_id = location_matches[0].location_id
        location = list(filter(lambda l: l.location_id == location_id, self.locations))[
            0
        ]

        # bundle the context
        return custom_types.SensorDataContext(
            sensor_id=sensor_id,
            serial_number=sensor.serial_number,
            utc_offset=utc_offset,
            pressure_calibration_factor=pressure_calibration_factor,
            date=date,
            location=location,
        )


def request_github_file(
    github_repository: str,
    filepath: str,
    access_token: Optional[str] = None,
) -> Any:
    """Sends a request and returns the content of the response, in unicode."""
    response = requests.get(
        f"https://raw.githubusercontent.com/{github_repository}/main/{filepath}",
        headers={
            "Authorization": f"token {access_token}",
            "Accept": "application/text",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.text


def load_remote_location_data(
    github_repository: str,
    access_token: Optional[str] = None,
) -> LocationDataInterface:
    """pass the github repo name as `org-name/repo-name`"""
    version = (
        request_github_file(
            github_repository, "pyproject.toml", access_token=access_token
        )
        .split("\n")[2]
        .split('"')[1]
    )

    data = {
        key: json.loads(
            request_github_file(
                github_repository,
                f"data/{key}.json",
                access_token=access_token,
            )
        )
        for key in ["locations", "sensors", "campaigns"]
    }

    return LocationDataInterface(version=version, **data)
