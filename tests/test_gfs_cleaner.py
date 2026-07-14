import os
import tempfile
import unittest
from pathlib import Path

from services.gfs_cleaner import cleanup_gfs_directory


class GfsCleanerTest(unittest.TestCase):
    def test_cleanup_keeps_only_the_latest_two_grib2_and_idx_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            directory = Path(tmp_dir)

            files = [
                ("gfs_20260709_06_f000.grib2", 100),
                ("gfs_20260709_12_f000.grib2", 200),
                ("gfs_20260710_06_f000.grib2", 300),
                ("gfs_20260710_12_f000.grib2", 400),
                ("gfs_20260709_06_f000.grib2.da267.idx", 100),
                ("gfs_20260709_12_f000.grib2.da267.idx", 200),
                ("gfs_20260710_06_f000.grib2.da267.idx", 300),
                ("gfs_20260710_12_f000.grib2.da267.idx", 400),
                ("readme.txt", 500),
            ]

            for name, timestamp in files:
                path = directory / name
                path.write_text(name)
                os.utime(path, (timestamp, timestamp))

            removed = cleanup_gfs_directory(directory)

            remaining = sorted(path.name for path in directory.iterdir() if path.is_file())
            self.assertEqual(
                remaining,
                [
                    "gfs_20260710_06_f000.grib2",
                    "gfs_20260710_06_f000.grib2.da267.idx",
                    "gfs_20260710_12_f000.grib2",
                    "gfs_20260710_12_f000.grib2.da267.idx",
                ],
            )
            self.assertEqual(
                removed,
                [
                    "gfs_20260709_06_f000.grib2",
                    "gfs_20260709_06_f000.grib2.da267.idx",
                    "gfs_20260709_12_f000.grib2",
                    "gfs_20260709_12_f000.grib2.da267.idx",
                    "readme.txt",
                ],
            )


if __name__ == "__main__":
    unittest.main()
