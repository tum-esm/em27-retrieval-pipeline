from __future__ import annotations
import datetime
import pydantic


class CalibrationFactors(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    sensor_id: str
    valid_from_datetime: datetime.datetime = pydantic.Field(...)
    valid_to_datetime: datetime.datetime = pydantic.Field(...)
    xco2: float = pydantic.Field(
        ..., description="Calibration factor for carbon dioxide: xco2_cal = xco2_raw * factor"
    )
    xch4: float = pydantic.Field(
        ..., description="Calibration factor for methane: xch4_cal = xch4_raw * factor"
    )
    xco: float = pydantic.Field(
        None, description="Calibration factor for carbon monoxide: xco_cal = xco_raw * factor"
    )
    xh2o: float = pydantic.Field(
        None, description="Calibration factor for water vapor: xh2o_cal = xh2o_raw * factor"
    )

    @pydantic.field_validator("root", mode="after")
    def validate(self, v: CalibrationFactors) -> CalibrationFactors:
        if v.valid_from_datetime >= v.valid_to_datetime:
            raise ValueError(
                f"valid_from_datetime {v.valid_from_datetime} should be less than valid_to_datetime {v.valid_to_datetime}"
            )
        return v


class CalibrationFactorsList(pydantic.RootModel[list[CalibrationFactors]]):
    root: list[CalibrationFactors]

    @pydantic.field_validator("root", mode="after")
    def validate(self, vs: list[CalibrationFactors]):
        sensor_ids = set([v.sensor_id for v in vs])
        for sensor_id in sensor_ids:
            sensor_values = sorted(
                [v for v in vs if v.sensor_id == sensor_id], key=lambda x: x.valid_from_datetime
            )
            for v1, v2 in zip(sensor_values[:-1], sensor_values[1:]):
                if v1.valid_to_datetime > v2.valid_from_datetime:
                    raise ValueError(
                        f"Overlapping calibration factors for sensor {sensor_id}: {v1.valid_to_datetime} > {v2.valid_from_datetime}"
                    )
