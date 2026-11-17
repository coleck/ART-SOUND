
# ============================================================
# ИМПОРТЫ
# ============================================================

import mimetypes

from pathlib import Path
from uuid import uuid4

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.artwork import Artwork

from app.repositories.artwork_repository import (
    get_all_artworks,
    get_artwork
)

from app.repositories.track_repository import get_all_tracks

from app.services.artwork_service import (
    add_artwork,
    publish_artwork,
    update_artwork
)

from app.services.track_service import (
    add_track,
    update_track_settings
)

from app.services.recommendation_service import (
    get_recommendations_for_artwork,
    generate_recommendations,
    review_recommendation,
    get_public_artwork
)

from app.services.qr_service import generate_qr_code


# ============================================================
# МОДЕЛИ ЗАПРОСОВ
# ============================================================

# Данные для одобрения или отклонения рекомендации.
class ReviewRequest(BaseModel):
    comment: str | None = None


# Данные для редактирования настроек музыкального трека.
class TrackUpdateRequest(BaseModel):
    title: str | None = None
    artist: str | None = None
    license_name: str | None = None
    license_url: str | None = None
    allowed_public_playback: bool | None = None
    is_active: bool | None = None


# ============================================================
# СОЗДАНИЕ FASTAPI-ПРИЛОЖЕНИЯ
# ============================================================

app = FastAPI(
    title="Music Painting System",
    description="Система сопоставления музыки с картинами",
    version="0.1.0"
)

# Настройки взаимодействия frontend и backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_origin_regex=r"https?://.*",
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# ОБЩИЕ МАРШРУТЫ
# ============================================================

# Главная страница API.
@app.get("/")
def home():
    return {
        "message": "Music Painting System API",
        "status": "running"
    }


# Проверка доступности сервера.
@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ============================================================
# НАСТРОЙКИ ХРАНЕНИЯ ФАЙЛОВ
# ============================================================

# Корневая папка проекта.
PROJECT_DIR = Path(__file__).resolve().parents[2]

# Папки для изображений и аудиофайлов.
ARTWORKS_DIR = PROJECT_DIR / "media" / "artworks"
TRACKS_DIR = PROJECT_DIR / "media" / "tracks"

# Разрешённые форматы изображений.
ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

# Разрешённые форматы аудиофайлов.
ALLOWED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".ogg",
    ".flac"
}

# Максимальные размеры загружаемых файлов.
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_AUDIO_SIZE = 30 * 1024 * 1024


# ============================================================
# РАБОТА С КАРТИНАМИ
# ============================================================

# Загрузка новой картины.
@app.post("/artworks")
async def create_new_artwork(
    title: str = Form(...),
    artist: str = Form(...),
    image: UploadFile = File(...),
    year: int | None = Form(None),
    description: str | None = Form(None),
    db: Session = Depends(get_db)
):
    # Проверяем формат изображения.
    extension = Path(image.filename or "").suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Неподдерживаемый формат изображения"
        )

    # Читаем файл с ограничением размера.
    image_data = await image.read(MAX_IMAGE_SIZE + 1)

    if not image_data:
        raise HTTPException(
            status_code=400,
            detail="Файл изображения пуст"
        )

    if len(image_data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Размер изображения не должен превышать 10 МБ"
        )

    # Создаём папку для изображений.
    ARTWORKS_DIR.mkdir(parents=True, exist_ok=True)

    # Формируем уникальное имя файла.
    filename = f"{uuid4().hex}{extension}"
    image_path = ARTWORKS_DIR / filename

    try:
        # Сохраняем изображение.
        image_path.write_bytes(image_data)

        # Создаём картину и выполняем анализ изображения.
        artwork = add_artwork(
            db=db,
            title=title,
            artist=artist,
            image_path=str(image_path),
            year=year,
            description=description
        )

        return {
            "message": "Картина успешно добавлена",
            "artwork": {
                "id": artwork.id,
                "title": artwork.title,
                "artist": artwork.artist,
                "year": artwork.year,
                "description": artwork.description,
                "status": artwork.status
            }
        }

    except Exception:
        # Удаляем файл, если создание записи завершилось ошибкой.
        if image_path.exists():
            image_path.unlink()

        raise

    finally:
        await image.close()


# Получение списка всех картин для административной работы.
@app.get("/artworks")
def read_artworks(db: Session = Depends(get_db)):
    artworks = get_all_artworks(db)

    return [
        {
            "id": artwork.id,
            "title": artwork.title,
            "artist": artwork.artist,
            "year": artwork.year,
            "description": artwork.description,
            "status": artwork.status
        }
        for artwork in artworks
    ]


# Получение одной картины по ID.
@app.get("/artworks/{artwork_id}")
def read_artwork(
    artwork_id: int,
    db: Session = Depends(get_db)
):
    artwork = get_artwork(db, artwork_id)

    if artwork is None:
        raise HTTPException(
            status_code=404,
            detail="Картина не найдена"
        )

    return {
        "id": artwork.id,
        "title": artwork.title,
        "artist": artwork.artist,
        "year": artwork.year,
        "description": artwork.description,
        "status": artwork.status
    }


# Публикация картины.
@app.post("/artworks/{artwork_id}/publish")
def publish_artwork_endpoint(
    artwork_id: int,
    db: Session = Depends(get_db)
):
    try:
        artwork = publish_artwork(
            db=db,
            artwork_id=artwork_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return {
        "message": "Картина успешно опубликована",
        "artwork_id": artwork.id,
        "status": artwork.status
    }


# Получение QR-кода картины.
@app.get("/artworks/{artwork_id}/qr")
def get_artwork_qr(
    artwork_id: int,
    db: Session = Depends(get_db)
):
    # Получаем картину из базы данных.
    artwork = db.get(Artwork, artwork_id)

    if artwork is None:
        raise HTTPException(
            status_code=404,
            detail="Картина не найдена"
        )

    # Создаём QR-код по уникальному токену картины.
    qr_path = generate_qr_code(str(artwork.qr_token))

    # Возвращаем PNG-файл.
    return FileResponse(
        path=qr_path,
        media_type="image/png",
        filename=f"artwork_{artwork.id}_qr.png"
    )


# ============================================================
# РАБОТА С МУЗЫКАЛЬНЫМИ ТРЕКАМИ
# ============================================================

# Загрузка нового музыкального трека.
@app.post("/tracks")
async def create_new_track(
    title: str = Form(...),
    artist: str | None = Form(None),
    license_name: str | None = Form(None),
    license_url: str | None = Form(None),
    allowed_public_playback: bool = Form(False),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Проверяем формат аудиофайла.
    extension = Path(audio.filename or "").suffix.lower()

    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Неподдерживаемый формат аудио"
        )

    # Читаем файл с ограничением размера.
    audio_data = await audio.read(MAX_AUDIO_SIZE + 1)

    if not audio_data:
        raise HTTPException(
            status_code=400,
            detail="Аудиофайл пуст"
        )

    if len(audio_data) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Размер аудиофайла не должен превышать 30 МБ"
        )

    # Создаём папку для музыкальных файлов.
    TRACKS_DIR.mkdir(parents=True, exist_ok=True)

    # Формируем уникальное имя файла.
    filename = f"{uuid4().hex}{extension}"
    audio_path = TRACKS_DIR / filename

    try:
        # Сохраняем аудиофайл.
        audio_path.write_bytes(audio_data)

        # Создаём трек и выполняем анализ аудио.
        track = add_track(
            db=db,
            title=title,
            file_path=str(audio_path),
            artist=artist,
            license_name=license_name,
            license_url=license_url,
            allowed_public_playback=allowed_public_playback
        )

        return {
            "message": "Аудиотрек успешно добавлен",
            "track": {
                "id": track.id,
                "title": track.title,
                "artist": track.artist,
                "duration_sec": track.duration_sec,
                "allowed_public_playback": track.allowed_public_playback,
                "is_active": track.is_active
            }
        }

    except Exception:
        # Удаляем файл, если создание трека завершилось ошибкой.
        if audio_path.exists():
            audio_path.unlink()

        raise

    finally:
        await audio.close()


# Получение списка всех музыкальных треков.
@app.get("/tracks")
def read_tracks(db: Session = Depends(get_db)):
    tracks = get_all_tracks(db)

    return [
        {
            "id": track.id,
            "title": track.title,
            "artist": track.artist,
            "duration_sec": track.duration_sec,
            "license_name": track.license_name,
            "license_url": track.license_url,
            "allowed_public_playback": track.allowed_public_playback,
            "is_active": track.is_active
        }
        for track in tracks
    ]


# Редактирование настроек музыкального трека.
@app.patch("/tracks/{track_id}")
def update_track(
    track_id: int,
    request: TrackUpdateRequest,
    db: Session = Depends(get_db)
):
    try:
        # Передаём в сервис только указанные поля.
        track = update_track_settings(
            db=db,
            track_id=track_id,
            updates=request.model_dump(exclude_unset=True)
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return {
        "message": "Настройки трека успешно обновлены",
        "track": {
            "id": track.id,
            "title": track.title,
            "artist": track.artist,
            "duration_sec": track.duration_sec,
            "license_name": track.license_name,
            "license_url": track.license_url,
            "allowed_public_playback": track.allowed_public_playback,
            "is_active": track.is_active
        }
    }


# ============================================================
# РАБОТА С МУЗЫКАЛЬНЫМИ РЕКОМЕНДАЦИЯМИ
# ============================================================

# Получение рекомендаций для конкретной картины.
@app.get("/artworks/{artwork_id}/recommendations")
def read_recommendations(
    artwork_id: int,
    db: Session = Depends(get_db)
):
    try:
        recommendations = get_recommendations_for_artwork(
            db=db,
            artwork_id=artwork_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    return [
        {
            "id": recommendation.id,
            "track": {
                "id": recommendation.track.id,
                "title": recommendation.track.title,
                "artist": recommendation.track.artist,
                "duration_sec": recommendation.track.duration_sec
            },
            "score": float(recommendation.score),
            "status": recommendation.status,
            "algorithm_version": recommendation.algorithm_version
        }
        for recommendation in recommendations
    ]


# Генерация рекомендаций для картины.
@app.post("/artworks/{artwork_id}/recommendations/generate")
def create_artwork_recommendations(
    artwork_id: int,
    db: Session = Depends(get_db)
):
    # Проверяем существование картины.
    artwork = get_artwork(db, artwork_id)

    if artwork is None:
        raise HTTPException(
            status_code=404,
            detail="Картина не найдена"
        )

    try:
        # Запускаем алгоритм сопоставления.
        recommendations = generate_recommendations(
            db=db,
            artwork_id=artwork_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return [
        {
            "id": recommendation.id,
            "track": {
                "id": recommendation.track.id,
                "title": recommendation.track.title,
                "artist": recommendation.track.artist,
                "duration_sec": recommendation.track.duration_sec
            },
            "score": float(recommendation.score),
            "status": recommendation.status,
            "algorithm_version": recommendation.algorithm_version
        }
        for recommendation in recommendations
    ]


# Одобрение музыкальной рекомендации.
@app.post("/recommendations/{recommendation_id}/approve")
def approve_recommendation(
    recommendation_id: int,
    request: ReviewRequest,
    db: Session = Depends(get_db)
):
    try:
        recommendation = review_recommendation(
            db=db,
            recommendation_id=recommendation_id,
            status="approved",
            comment=request.comment
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    return {
        "message": "Рекомендация одобрена",
        "id": recommendation.id,
        "artwork_id": recommendation.artwork_id,
        "track_id": recommendation.track_id,
        "score": float(recommendation.score),
        "status": recommendation.status
    }


# Отклонение музыкальной рекомендации.
@app.post("/recommendations/{recommendation_id}/reject")
def reject_recommendation(
    recommendation_id: int,
    request: ReviewRequest,
    db: Session = Depends(get_db)
):
    try:
        recommendation = review_recommendation(
            db=db,
            recommendation_id=recommendation_id,
            status="rejected",
            comment=request.comment
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    return {
        "message": "Рекомендация отклонена",
        "id": recommendation.id,
        "artwork_id": recommendation.artwork_id,
        "track_id": recommendation.track_id,
        "score": float(recommendation.score),
        "status": recommendation.status
    }


# ============================================================
# ПУБЛИЧНАЯ ЧАСТЬ — ДОСТУП ПО QR-КОДУ
# ============================================================

# Получение информации о картине и одобренной музыке.
@app.get("/public/artworks/{qr_token}")
def read_public_artwork(
    qr_token: str,
    db: Session = Depends(get_db)
):
    try:
        artwork, recommendation = get_public_artwork(
            db=db,
            qr_token=qr_token
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    track = recommendation.track

    return {
        "artwork": {
            "id": artwork.id,
            "title": artwork.title,
            "artist": artwork.artist,
            "year": artwork.year,
            "description": artwork.description
        },
        "music": {
            "id": track.id,
            "title": track.title,
            "artist": track.artist,
            "duration_sec": track.duration_sec,
            "score": float(recommendation.score)
        }
    }


# Получение аудиофайла для воспроизведения.
@app.get("/public/artworks/{qr_token}/audio")
def read_public_artwork_audio(
    qr_token: str,
    db: Session = Depends(get_db)
):
    try:
        artwork, recommendation = get_public_artwork(
            db=db,
            qr_token=qr_token
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    track = recommendation.track
    audio_path = Path(track.file_path)

    # Проверяем наличие аудиофайла.
    if not audio_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Аудиофайл не найден"
        )

    # Определяем MIME-тип по расширению файла.
    media_type, _ = mimetypes.guess_type(str(audio_path))

    return FileResponse(
        path=audio_path,
        media_type=media_type or "application/octet-stream",
        filename=audio_path.name
    )

@app.patch("/artworks/{artwork_id}")
def edit_artwork(
    artwork_id: int,
    updates: dict,
    db: Session = Depends(get_db)
):
    try:
        artwork = update_artwork(
            db=db,
            artwork_id=artwork_id,
            updates=updates
        )

        return {
            "message": "Информация о картине обновлена.",
            "artwork": {
                "id": artwork.id,
                "title": artwork.title,
                "artist": artwork.artist,
                "year": artwork.year,
                "description": artwork.description,
                "status": artwork.status
            }
        }

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) 
# Получение изображения картины.
@app.get("/public/artworks/{qr_token}/image")
def read_public_artwork_image(
    qr_token: str,
    db: Session = Depends(get_db)
):
    try:
        artwork, recommendation = get_public_artwork(
            db=db,
            qr_token=qr_token
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    # Проверяем наличие пути к изображению.
    if not artwork.image_path:
        raise HTTPException(
            status_code=404,
            detail="Путь к изображению не указан"
        )

    image_path = Path(artwork.image_path)

    # Проверяем наличие самого файла.
    if not image_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Изображение картины не найдено"
        )

    # Определяем MIME-тип изображения.
    media_type, _ = mimetypes.guess_type(str(image_path))

    return FileResponse(
        path=image_path,
        media_type=media_type or "application/octet-stream"
    )
