from dataclasses import dataclass
from datetime import datetime

@dataclass
class Query:
    t_from_int: int
    t_to_int: int
    sensor: str
    location: str
    serial_number: str
    lat: float
    lon: float

    @property
    def t_from_str(self):
        return str(self.t_from_int)
    
    @property
    def t_from_datetime(self):
        return datetime.strptime(str(self.t_from_int), "%Y%m%d")

    @t_from_datetime.setter
    def t_from_datetime(self, t):
        self.t_from_int = int(datetime.strftime(t, "%Y%m%d"))
    
    @property
    def t_to_str(self):
        return str(self.t_to_int)
    
    @property
    def t_to_datetime(self):
        return datetime.strptime(str(self.t_to_int), "%Y%m%d")

    @t_to_datetime.setter
    def t_to_datetime(self, t: datetime):
        self.t_to_int = int(datetime.strftime(t, "%Y%m%d"))
    
    def to_json(self):
        return {
            "t_from_int": self.t_from_int,
            "t_to_int": self.t_to_int,
            "sensor": self.sensor,
            "location": self.location,
            "serial_number": self.serial_number,
            "lat": self.lat,
            "lon": self.lon,
        }


    def clone(self):
        return Query(
            t_from_int=self.t_from_int,
            t_to_int= self.t_to_int,
            sensor= self.sensor,
            location= self.location,
            serial_number= self.serial_number,
            lat= self.lat,
            lon= self.lon,
        )
