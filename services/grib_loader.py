from pathlib import Path
import numpy as np
import xarray as xr

from models.wind_grid import WindGrid


class GribLoader:
    def load(self, path: str | Path) -> WindGrid | None:
        path = Path(path)
        
        with xr.open_dataset(
            path, 
                engine="cfgrib",
                backend_kwargs={
                    "filter_by_keys": {
                        "typeOfLevel": "heightAboveGround",
                        "level": 10,
                    }
                }, 
            ) as ds:
            required = ("u10", "v10")

            print(ds)
            print(ds.data_vars)

            for name in required:
                if name not in ds:
                    raise RuntimeError(f"{name} не найдено в файле {path}")
                
            u = ds["u10"].values.astype(np.float32)
            v = ds["v10"].values.astype(np.float32)
        
            latitudes = ds.latitude.values
            longitudes = ds.longitude.values
        
        longitudes = ((longitudes + 180) % 360) - 180

        order = np.argsort(longitudes)
        longitudes = longitudes[order]
        u = u[:, order]
        v = v[:, order]

        latitudes = latitudes[::-1]
        u = u[::-1, :]
        v = v[::-1, :]
        
        if u.shape != v.shape:
            raise ValueError(
                f"Не совпадают размеры: u={u.shape}, v={v.shape}"
            )

        ny, nx = u.shape

        dx = float(abs(longitudes[1] - longitudes[0]))
        dy = float(abs(latitudes[1] - latitudes[0]))

        return WindGrid(
            min_lon=float(longitudes.min()),
            max_lon=float(longitudes.max()),
            min_lat=float(latitudes.min()),
            max_lat=float(latitudes.max()),
            dx=dx,
            dy=dy,
            nx=nx,
            ny=ny,
            u=u,
            v=v,
        )