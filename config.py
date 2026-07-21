from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()

HOME = Path.home()
SOURCE_FOLDER = PROJECT_ROOT.parent /"wind-data-service" / "data"
NPZ_FILE_NAME = "windgrid.npz"
CURRENT_CYCLE_JSON_PATH = SOURCE_FOLDER / "current_cycle.json"
NPZ_PATH = SOURCE_FOLDER / NPZ_FILE_NAME