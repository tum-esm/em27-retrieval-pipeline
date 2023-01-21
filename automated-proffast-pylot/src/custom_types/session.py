from pydantic import BaseModel


class Session(BaseModel):
    sensor_id: str
    location_id: str
    date: str
    lat: float
    lon: float
    alt: int
    serial_number: int
    utc_offset: float
    container_id: str
    container_path: str
