from pydantic import BaseModel
from .location_data import Location
from .pylot_container import PylotContainer


class SensorDataContext(BaseModel):
    sensor_id: str
    serial_number: int
    utc_offset: float
    date: str
    location: Location


class Session(BaseModel):
    sensor_data_context: SensorDataContext
    pylot_container: PylotContainer
