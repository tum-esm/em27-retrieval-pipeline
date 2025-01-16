from __future__ import annotations
import os
import dotenv
import pydantic
import tum_esm_utils


class GEOMSGeneralMetadata(pydantic.BaseModel):
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


class GEOMSDataMetadata(pydantic.BaseModel):
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


class GEOMSFileMetadata(pydantic.BaseModel):
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


class GEOMSContactlMetadata(pydantic.BaseModel):
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


class GEOMSMetadata(pydantic.BaseModel):
    general: GEOMSGeneralMetadata
    data: GEOMSDataMetadata
    file: GEOMSFileMetadata
    principle_investigator: GEOMSContactlMetadata
    data_originator: GEOMSContactlMetadata
    data_submitter: GEOMSContactlMetadata
    locations: dict[str, str] = pydantic.Field(
        ..., description="Maps your locations id to the corresponding EVDC location id"
    )

    @staticmethod
    def load(template: bool = False) -> GEOMSMetadata:
        """Load the EVDC metadata from `<config_dir>/geoms_metadata.json`."""

        erp_config_dir = tum_esm_utils.files.rel_to_abs_path("../../config")
        if not template:
            env_path = os.path.join(tum_esm_utils.files.rel_to_abs_path("../../config"), ".env")
            if os.path.isfile(env_path):
                dotenv.load_dotenv(env_path)
            erp_config_dir = os.getenv("ERP_CONFIG_DIR", erp_config_dir)
        filepath = os.path.join(
            erp_config_dir, f"geoms_metadata{'.template' if template else ''}.json"
        )
        return GEOMSMetadata.model_validate_json(tum_esm_utils.files.load_file(filepath))
