from pydantic import BaseModel
import tum_esm_em27_metadata.types


class PylotContainer(BaseModel):
    container_id: str
    container_path: str
    data_input_path: str
    data_output_path: str
    pylot_config_path: str
    pylot_log_format_path: str

    class Config:
        extra = "ignore"


class Session(BaseModel):
    sensor_id: str
    serial_number: int
    utc_offset: float
    pressure_data_source: str
    pressure_calibration_factor: float
    date: str
    location: tum_esm_em27_metadata.types.Location
    container_id: str
    container_path: str
    data_input_path: str
    data_output_path: str
    pylot_config_path: str
    pylot_log_format_path: str

    class Config:
        extra = "ignore"
