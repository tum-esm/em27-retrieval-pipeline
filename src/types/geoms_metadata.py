from __future__ import annotations

import datetime
import os
from typing import Optional

import dotenv
import pydantic
import tomli
import tum_esm_utils

from .basic_types import UTC_DATETIME_STRING_PATTERN, parse_datetime_string
from .old_schemas import OldGEOMSMetadata, OldCalibrationFactorsList


class GEOMSMetadataFields:
    class General(pydantic.BaseModel):
        network: str = pydantic.Field(
            ...,
            description="Used in the filename of the HDF5 file",
            examples=["FTIR.COCCON"],
        )
        affiliation: str = pydantic.Field(
            ...,
            description="Used in the filename of the HDF5 file",
            examples=["TUM.ESM"],
        )
        pressure_sensor_name: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `SURFACE.PRESSURE_INDEPENDENT_SOURCE`",
            examples=["young-61302", "vaisala-PTB330"],
        )

    class Data(pydantic.BaseModel):
        discipline: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `DATA_DISCIPLINE`",
            examples=["ATMOSPHERIC.CHEMISTRY;REMOTE.SENSING;GROUNDBASED"],
        )
        group: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `DATA_GROUP`",
            examples=["EXPERIMENTAL;PROFILE.STATIONARY"],
        )
        file_version: int = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `DATA_FILE_VERSION`",
            examples=[1],
        )
        quality: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `DATA_QUALITY`",
            examples=["Station data."],
        )
        template: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `DATA_TEMPLATE`",
            examples=["GEOMS-TE-FTIR-COCCON-001"],
        )

    class File(pydantic.BaseModel):
        doi: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `FILE_DOI`",
        )
        meta_version: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `FILE_META_VERSION`",
            examples=["04R088;CUSTOM"],
        )
        access: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `FILE_ACCESS`",
            examples=["COCCON"],
        )
        project_id: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `FILE_PROJECT_ID`",
            examples=["COCCON"],
        )

    class Contact(pydantic.BaseModel):
        name: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `PI_NAME`/`DO_NAME`/`DS_NAME`",
            examples=["Makowski;Moritz"],
        )
        email: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `PI_EMAIL`/`DO_EMAIL`/`DS_EMAIL`",
            examples=["moritz.makowski@tum.de"],
        )
        affiliation: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `PI_AFFILIATION`/`DO_AFFILIATION`/`DS_AFFILIATION`",
            examples=[
                "Technical University of Munich - Professorship of Environmental Sensing and Modeling;TUM.ESM"
            ],
        )
        address: str = pydantic.Field(
            ...,
            description="The value of the HDF5 attribute `PI_ADDRESS`/`DO_ADDRESS`/`DS_ADDRESS`",
            examples=["Theresienstr. 90;D-80333 Munich;GERMANY"],
        )

    class CalibrationFactors(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

        sensor_id: str
        valid_from_datetime: str = pydantic.Field(
            ...,
            pattern=UTC_DATETIME_STRING_PATTERN,
            description="UTC datetime in format `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS+0000`.",
        )
        valid_to_datetime: str = pydantic.Field(
            ...,
            pattern=UTC_DATETIME_STRING_PATTERN,
            description="UTC datetime in format `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS+0000`.",
        )
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

        @pydantic.model_validator(mode="after")
        def validate_times(self) -> GEOMSMetadataFields.CalibrationFactors:
            if self.valid_from_datetime_parsed >= self.valid_to_datetime_parsed:
                raise ValueError(
                    f"valid_from_datetime {self.valid_from_datetime} should be less than valid_to_datetime {self.valid_to_datetime}"
                )
            return self

        @property
        def valid_from_datetime_parsed(self) -> datetime.datetime:
            return parse_datetime_string(self.valid_from_datetime)

        @property
        def valid_to_datetime_parsed(self) -> datetime.datetime:
            return parse_datetime_string(self.valid_to_datetime)

    class CalibrationFactorsList(pydantic.RootModel[list[CalibrationFactors]]):
        root: list[GEOMSMetadataFields.CalibrationFactors]

        @pydantic.model_validator(mode="after")
        def validate_sensor_ids(self) -> GEOMSMetadataFields.CalibrationFactorsList:
            sensor_ids = {v.sensor_id for v in self.root}
            for sensor_id in sensor_ids:
                sensor_values = sorted(
                    [v for v in self.root if v.sensor_id == sensor_id],
                    key=lambda x: x.valid_from_datetime_parsed,
                )
                for v1, v2 in zip(sensor_values[:-1], sensor_values[1:]):
                    if v1.valid_to_datetime_parsed > v2.valid_from_datetime_parsed:
                        raise ValueError(
                            f"Overlapping calibration factors for sensor {sensor_id}: {v1.valid_to_datetime} > {v2.valid_from_datetime}"
                        )
            return self

        def get_index(self, sensor_id: str, datetime: datetime.datetime) -> Optional[int]:
            """Get the calibration factors for the specified sensor."""
            try:
                return next(
                    i
                    for i, v in enumerate(self.root)
                    if v.sensor_id == sensor_id
                    and v.valid_from_datetime_parsed <= datetime
                    and v.valid_to_datetime_parsed >= datetime
                )
            except StopIteration:
                return None


class GEOMSMetadata(pydantic.BaseModel):
    general: GEOMSMetadataFields.General
    data: GEOMSMetadataFields.Data
    file: GEOMSMetadataFields.File
    principle_investigator: GEOMSMetadataFields.Contact
    data_originator: GEOMSMetadataFields.Contact
    data_submitter: GEOMSMetadataFields.Contact
    locations: dict[str, str] = pydantic.Field(
        ..., description="Maps your locations id to the corresponding EVDC location id"
    )
    calibration_factors: GEOMSMetadataFields.CalibrationFactorsList

    @staticmethod
    def load(template: bool = False) -> GEOMSMetadata:
        """Load the EVDC metadata from `<config_dir>/geoms_metadata.toml`."""

        erp_config_dir = tum_esm_utils.files.rel_to_abs_path("../../config")
        if not template:
            env_path = os.path.join(tum_esm_utils.files.rel_to_abs_path("../../config"), ".env")
            if os.path.isfile(env_path):
                dotenv.load_dotenv(env_path)
            erp_config_dir = os.getenv("ERP_CONFIG_DIR", erp_config_dir)
        erp_config_dir = os.path.abspath(erp_config_dir)
        filepath = os.path.join(
            erp_config_dir, f"geoms_metadata{'.template' if template else ''}.toml"
        )

        if os.path.isfile(filepath):
            with open(filepath, "rb") as file:
                return GEOMSMetadata.model_validate(tomli.load(file))

        geoms_metadata_path = os.path.join(erp_config_dir, "geoms_metadata.json")
        calibration_factors_path = os.path.join(erp_config_dir, "calibration_factors.json")
        if not os.path.isfile(geoms_metadata_path):
            raise FileNotFoundError(
                f"Did not find {filepath}. Also did not find old format at {geoms_metadata_path}."
            )
        if not os.path.isfile(calibration_factors_path):
            raise FileNotFoundError(
                f"Did not find {filepath}. Also did not find old format at {calibration_factors_path}."
            )

        old_metadata = OldGEOMSMetadata.model_validate_json(
            tum_esm_utils.files.load_file(geoms_metadata_path)
        )
        old_calibration_factors = OldCalibrationFactorsList.model_validate_json(
            tum_esm_utils.files.load_file(calibration_factors_path)
        )

        new_geoms_metadata = GEOMSMetadata.model_validate(
            {
                **old_metadata.model_dump(mode="json"),
                "calibration_factors": old_calibration_factors.model_dump(mode="json"),
            }
        )
        tmp_filepath = filepath.removesuffix(".toml") + ".tmp.toml"
        tum_esm_utils.files.dump_toml_file(
            tmp_filepath, new_geoms_metadata.model_dump(mode="json", exclude_none=True)
        )
        os.replace(tmp_filepath, filepath)
        return new_geoms_metadata
