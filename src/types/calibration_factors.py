from __future__ import annotations
import datetime
import os
from typing import Optional
import dotenv
import pydantic
import tum_esm_utils


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
        ..., description="Calibration factor for carbon monoxide: xco_cal = xco_raw * factor"
    )
    xh2o: float = pydantic.Field(
        ..., description="Calibration factor for water vapor: xh2o_cal = xh2o_raw * factor"
    )

    @staticmethod
    @pydantic.field_validator("root", mode="after")
    def validate_times(v: CalibrationFactors) -> CalibrationFactors:
        if v.valid_from_datetime >= v.valid_to_datetime:
            raise ValueError(
                f"valid_from_datetime {v.valid_from_datetime} should be less than valid_to_datetime {v.valid_to_datetime}"
            )
        return v


class CalibrationFactorsList(pydantic.RootModel[list[CalibrationFactors]]):
    root: list[CalibrationFactors]

    @staticmethod
    @pydantic.field_validator("root", mode="after")
    def validate_sensor_ids(vs: CalibrationFactorsList) -> CalibrationFactorsList:
        sensor_ids = set([v.sensor_id for v in vs.root])
        for sensor_id in sensor_ids:
            sensor_values = sorted(
                [v for v in vs.root if v.sensor_id == sensor_id],
                key=lambda x: x.valid_from_datetime,
            )
            for v1, v2 in zip(sensor_values[:-1], sensor_values[1:]):
                if v1.valid_to_datetime > v2.valid_from_datetime:
                    raise ValueError(
                        f"Overlapping calibration factors for sensor {sensor_id}: {v1.valid_to_datetime} > {v2.valid_from_datetime}"
                    )
        return vs

    @staticmethod
    def load(template: bool = False) -> CalibrationFactorsList:
        """Load the calibration factors from `<config_dir>/calibration_factors.json`."""

        erp_config_dir = tum_esm_utils.files.rel_to_abs_path("../../config")
        if not template:
            env_path = os.path.join(tum_esm_utils.files.rel_to_abs_path("../../config"), ".env")
            if os.path.isfile(env_path):
                dotenv.load_dotenv(env_path)
            erp_config_dir = os.getenv("ERP_CONFIG_DIR", erp_config_dir)
        filepath = os.path.join(
            erp_config_dir, f"calibration_factors{'.template' if template else ''}.json"
        )
        return CalibrationFactorsList.model_validate_json(tum_esm_utils.files.load_file(filepath))

    def get_index(self, sensor_id: str, datetime: datetime.datetime) -> Optional[int]:
        """Get the calibration factors for the specified sensor."""
        try:
            return next(
                i
                for i, v in enumerate(self.root)
                if v.sensor_id == sensor_id
                and v.valid_from_datetime <= datetime
                and v.valid_to_datetime >= datetime
            )
        except StopIteration:
            return None
