from dataclasses import dataclass
from datetime import datetime, timedelta
from src.utils import load_setup

PROJECT_DIR, CONFIG = load_setup(validate=False)

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
    
    @property
    def date_string_list(self) -> list[str]:
        l = []
        q = self.clone()
        while q.t_from_datetime <= self.t_to_datetime:
            l.append(q.t_from_str)
            q.t_from_datetime += timedelta(days=1)
        del q
        return l
    
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
