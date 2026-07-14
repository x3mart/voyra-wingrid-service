import os
import datetime
import requests
from pathlib import Path

GFS_BASE_URL = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"


def get_cache_path(subdir, filename):
    path = Path('./data/') / subdir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def is_stale(filepath, max_age_seconds=3600):
    if not os.path.exists(filepath):
        return True
    age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
    return age.total_seconds() > max_age_seconds



def download_gfs_wind():
    """Скачивает самый свежий GFS 0.25° f000"""
    now = datetime.datetime.now(datetime.timezone.utc)
    for hours_back in range(0, 48, 6):
        dt = now - datetime.timedelta(hours=hours_back)
        cycle = (dt.hour // 6) * 6
        yyyymmdd = dt.strftime("%Y%m%d")
        hh = f"{cycle:02d}"
        url = f"{GFS_BASE_URL}/gfs.{yyyymmdd}/{hh}/atmos/gfs.t{hh}z.pgrb2.0p25.f000"
        filename = f"gfs_{yyyymmdd}_{hh}_f000.grib2"
        filepath = get_cache_path("gfs", filename)

        if os.path.exists(filepath) and not is_stale(filepath, 43200):  # 12 часов
            return filepath

        try:
            r = requests.get(url, stream=True, timeout=40)
            if r.status_code == 200:
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                return filepath
        except Exception:
            continue
    raise RuntimeError("Не удалось скачать GFS")