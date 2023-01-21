from pydantic import BaseModel


class SessionDict(BaseModel):
    sensor: str
    location: str
    date: str
    lat: float
    lon: float
    alt: int
    serial_number: int
    utc_offset: float
    container_id: str
    container_path: str
