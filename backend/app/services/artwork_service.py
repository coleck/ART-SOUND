
from pathlib import Path

from sqlalchemy.orm import Session

from app.analysis.image.image_analysis import analyze_image
from app.models.artwork import Artwork
from app.models.recommendation import Recommendation
from app.models.audio_track import AudioTrack
from app.repositories.artwork_repository import (
    create_artwork,
    save_artwork_features
)


def add_artwork(
    db: Session,
    title: str,
    artist: str,
    image_path: str,
    year: int | None = None,
    description: str | None = None,
    created_by: int | None = None
):
    try:
        artwork = create_artwork(
            db=db,
            title=title,
            artist=artist,
            image_path=image_path,
            year=year,
            description=description,
            created_by=created_by
        )

        features = analyze_image(image_path)

        save_artwork_features(
            db=db,
            artwork_id=artwork.id,
            features=features
        )

        db.commit()
        db.refresh(artwork)

        return artwork

    except Exception:
        db.rollback()
        raise


def update_artwork(
    db: Session,
    artwork_id: int,
    updates: dict
):
    allowed_fields = {
        "title",
        "artist",
        "year",
        "description"
    }

    unknown_fields = set(updates) - allowed_fields

    if unknown_fields:
        raise ValueError("Переданы недопустимые поля.")

    if not updates:
        raise ValueError("Не указаны поля для обновления.")

    try:
        artwork = db.query(Artwork).filter(
            Artwork.id == artwork_id
        ).first()

        if artwork is None:
            raise LookupError("Картина не найдена.")

        for field, value in updates.items():
            if field in ("title", "artist"):
                if value is None or not value.strip():
                    raise ValueError(
                        f"Поле {field} не может быть пустым."
                    )
                value = value.strip()

            elif field == "description":
                value = value.strip() or None if value else None

            setattr(artwork, field, value)

        db.commit()
        db.refresh(artwork)

        return artwork

    except Exception:
        db.rollback()
        raise


def publish_artwork(db: Session, artwork_id: int):
    try:
        artwork = db.query(Artwork).filter(
            Artwork.id == artwork_id
        ).first()

        if artwork is None:
            raise ValueError("Картина не найдена.")

        recommendation = (
            db.query(Recommendation)
            .join(AudioTrack)
            .filter(
                Recommendation.artwork_id == artwork_id,
                Recommendation.status == "approved"
            )
            .first()
        )

        if recommendation is None:
            raise ValueError(
                "Для картины нет одобренной музыкальной композиции."
            )

        track = recommendation.track

        if not track.is_active:
            raise ValueError("Выбранный трек неактивен.")

        if not track.allowed_public_playback:
            raise ValueError(
                "Для трека не разрешено публичное воспроизведение."
            )

        if not Path(artwork.image_path).is_file():
            raise ValueError("Файл изображения не найден.")

        if not Path(track.file_path).is_file():
            raise ValueError("Файл аудиозаписи не найден.")

        artwork.status = "published"

        db.commit()
        db.refresh(artwork)

        return artwork

    except Exception:
        db.rollback()
        raise
