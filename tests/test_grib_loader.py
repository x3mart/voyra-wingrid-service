import unittest
from pathlib import Path

import numpy as np
import xarray as xr

from services.grib_loader import GribLoader


class GribLoaderOrientationTest(unittest.TestCase):
    def test_loader_flips_latitude_axis_to_ascending_order(self):
        path = Path("data/gfs/gfs_20260712_06_f000.grib2")

        with xr.open_dataset(
            path,
            engine="cfgrib",
            backend_kwargs={"filter_by_keys": {"typeOfLevel": "heightAboveGround", "level": 10}},
        ) as ds:
            raw_u = ds["u10"].values.astype(np.float32)
            raw_v = ds["v10"].values.astype(np.float32)
            longitudes = ds.longitude.values

        longitudes = ((longitudes + 180) % 360) - 180
        order = np.argsort(longitudes)
        expected_u = raw_u[:, order][::-1]
        expected_v = raw_v[:, order][::-1]

        grid = GribLoader().load(path)

        self.assertIsNotNone(grid)
        self.assertTrue(np.allclose(grid.u, expected_u))
        self.assertTrue(np.allclose(grid.v, expected_v))


if __name__ == "__main__":
    unittest.main()
