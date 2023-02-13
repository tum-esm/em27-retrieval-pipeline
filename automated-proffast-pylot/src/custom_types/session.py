from pydantic import BaseModel
from .location_data import Location


class SensorDataContext(BaseModel):
    sensor_id: str
    serial_number: int
    utc_offset: float
    pressure_calibration_factor: float
    date: str
    location: Location


class PylotContainer(BaseModel):
    container_id: str
    container_path: str
    data_input_path: str
    data_output_path: str
    pylot_config_path: str
    pylot_log_format_path: str


class Session(BaseModel):
    sensor_id: str
    serial_number: int
    utc_offset: float
    pressure_calibration_factor: float
    date: str
    location: Location
    container_id: str
    container_path: str
    data_input_path: str
    data_output_path: str
    pylot_config_path: str
    pylot_log_format_path: str
