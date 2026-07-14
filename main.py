import asyncio
import os
import glob
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends #type: ignore

from models.wind_grid import WindGrid
from models.wind_grid_response import WindGridResponse
from models.wind_request import WindRequest
from api.noaa_gfs_dowload import download_gfs_wind
from services.get_wind_grid import get_wind_grid
from services.grib_loader import GribLoader
from services.gfs_cleaner import cleanup_gfs_directory


def get_latest_grib_file() -> Path | None:
    """Находит самый свежий скачанный grib-файл в папке"""
    list_of_files = glob.glob('data/gfs/*.grib2')
    if not list_of_files:
        return None
    # Сортируем по времени изменения и берем самый свежий
    latest_file = max(list_of_files, key=os.path.getmtime)
    return Path(latest_file)

# 1. Функция загрузки
async def load_latest_grib(path: Path) -> WindGrid | None:
    loader = GribLoader()
    return loader.load(path)

# 2. Фоновый цикл обновления
async def wind_grid_updater(app: FastAPI, initial_grid: WindGrid | None):
    app.state.wind_grid = initial_grid
    
    # Запоминаем путь и mtime файла, который мы загрузили при старте
    current_file = get_latest_grib_file()
    last_mtime = os.path.getmtime(current_file) if current_file else 0
    last_path = current_file
    
    while True:
        await asyncio.sleep(300) # Проверяем папку каждые 5 минут
        
        try:
            latest_file = get_latest_grib_file()
            if latest_file:
                current_mtime = os.path.getmtime(latest_file)
                
                # Если путь к файлу изменился (наступили новые 6 часов) ИЛИ обновился старый файл
                if latest_file != last_path or current_mtime != last_mtime or app.state.wind_grid is None:
                    print(f"[Memory Worker] Обнаружен новый файл прогноза: {latest_file}. Парсим...")
                    
                    new_grid = await load_latest_grib(latest_file)
                    app.state.wind_grid = new_grid
                    
                    # Обновляем маркеры
                    last_mtime = current_mtime
                    last_path = latest_file
                    if new_grid is not None:
                        print(f"[Memory Worker] Сетка ветра в app.state успешно обновлена! RAM: {new_grid.memory_usage_mb} MB")
        except Exception as e:
            print(f"[Memory Worker] Ошибка при обновлении сетки в памяти: {e}")


# 3. Фоновый цикл скачивания gfs с NOAA
async def wind_downloader_loop():
    """Фоновый воркер для скачивания свежих файлов GFS с NOAA"""
    print("[Downloader] Фоновый воркер скачивания запущен.")
    while True:
        try:
            print("[Downloader] Проверяем наличие обновлений GFS на сервере...")
            # Выносим синхронный requests.get в отдельный поток
            latest_filepath = await asyncio.to_thread(download_gfs_wind)
            print(f"[Downloader] Проверка завершена. Актуальный файл на диске: {latest_filepath}")
        except Exception as e:
            print(f"[Downloader] Ошибка при скачивании GFS: {e}")
        
        # Модели GFS обновляются раз в 6 часов, но сам процесс релиза на серверах NOAA 
        # может задерживаться. Проверяем сервер каждые 60 минут.
        await asyncio.sleep(3600)
        

async def gfs_cleanup_loop():
    """Очищает папку с GFS один раз при старте и затем раз в сутки."""
    print("[Cleaner] Фоновый воркер очистки запущен.")

    while True:
        try:
            removed_files = cleanup_gfs_directory()
            if removed_files:
                print(f"[Cleaner] Удалено {len(removed_files)} старых файлов GFS: {', '.join(removed_files)}")
            else:
                print("[Cleaner] Очистка завершена.")
        except Exception as e:
            print(f"[Cleaner] Ошибка при очистке GFS: {e}")

        await asyncio.sleep(86400)


# 3. САМ LIFESPAN (Обязательно ПЕРЕД созданием app = FastAPI)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. При старте проверяем, есть ли на диске уже скачанный ранее файл
    start_grid = None
    latest_file = get_latest_grib_file()
    
    if latest_file:
        try:
            print(f"[Lifespan] Найдена сохраненная модель {latest_file}. Загружаем при старте...")
            start_grid = await load_latest_grib(latest_file)
        except Exception as e:
            print(f"[Lifespan] Не удалось прочитать существующий файл: {e}")
            
    # 2. Запускаем воркер обновления памяти (передаем стартовую сетку)
    memory_task = asyncio.create_task(wind_grid_updater(app, start_grid))
    
    # 3. Запускаем воркер скачивания файлов с NOAA
    download_task = asyncio.create_task(wind_downloader_loop())

    # 4. Запускаем воркер очистки папки GFS
    cleanup_task = asyncio.create_task(gfs_cleanup_loop())
    
    yield # Сервер FastAPI успешно запущен и принимает запросы
    
    # При остановке сервера отменяем обе задачи
    memory_task.cancel()
    download_task.cancel()
    cleanup_task.cancel()


app = FastAPI(lifespan=lifespan)



@app.get("/f-api/v2/wind-grid")
async def get_wind(
    request: WindRequest = Depends(),
):
    wind_grid = get_wind_grid(app)

    return wind_grid.resample(
        request,
    )