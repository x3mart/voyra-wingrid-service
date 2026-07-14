from fastapi import FastAPI, HTTPException

from models.wind_grid import WindGrid


def get_wind_grid(app: FastAPI) -> WindGrid:
    wind_grid = getattr(app.state, "wind_grid", None)
    if wind_grid is None:
        raise HTTPException(status_code=503, detail="Данные ветра еще загружаются")
    return wind_grid