from __future__ import annotations

from pathlib import Path


def cleanup_gfs_directory(directory: str | Path | None = None) -> list[str]:
    """Удаляет старые файлы из каталога GFS, оставляя последние 2 GRIB2 и 2 IDX."""
    if directory is None:
        directory = Path(__file__).resolve().parents[1] / "data" / "gfs"

    directory = Path(directory)
    if not directory.exists():
        return []

    files = [path for path in directory.iterdir() if path.is_file()]
    if not files:
        return []

    grib2_files = sorted(
        [path for path in files if path.suffix == ".grib2"],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    idx_files = sorted(
        [path for path in files if path.name.endswith(".idx")],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    keep_paths = {
        path.resolve() for path in grib2_files[:2] + idx_files[:2]
    }

    removed_names: list[str] = []
    for path in files:
        if path.resolve() in keep_paths:
            continue
        path.unlink(missing_ok=True)
        removed_names.append(path.name)

    removed_names.sort()
    return removed_names
