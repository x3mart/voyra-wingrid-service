from pydantic import BaseModel


class WindPoint(BaseModel):
    lat: float
    lon: float
    u: float
    v: float