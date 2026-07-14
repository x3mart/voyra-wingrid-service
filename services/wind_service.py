from models.wind_grid import WindGrid
from services.grib_loader import GribLoader


class WindService:
    def __init__(self) -> None:
        self.grid: WindGrid | None = None

    def load(self, path: str):
        self.grid = GribLoader().load(path)

    def get_grid(self) -> WindGrid | None:
        return self.grid