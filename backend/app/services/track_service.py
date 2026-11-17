from sqlalchemy.orm import Session
from app.analysis.audio.audio_analysis import analyze_audio

from app.repositories.track_repository import (
    create_track,
    save_track_features,
    get_track
)
from app.services.artwork_service import (
    add_artwork,
    publish_artwork,
    update_artwork
)

def add_track(
    db: Session,
    title: str,
    file_path: str,
    artist: str | None = None,
    duration_sec: int | None = None,
    license_name: str | None = None,
    license_url: str | None = None,
    allowed_public_playback: bool = False,
    created_by: int | None = None
):
    try:
        track = create_track(
            db=db,
            title=title,
            file_path=file_path,
            artist=artist,
            duration_sec=duration_sec,
            license_name=license_name,
            license_url=license_url,
            allowed_public_playback=allowed_public_playback,
            created_by=created_by
        )

        features = analyze_audio(file_path)

        track.duration_sec = int(features["duration_sec"])

        save_track_features(
            db=db,
            track_id=track.id,
            features=features
        )

        db.commit()
        db.refresh(track)

        return track

    except Exception:
        db.rollback()
        raise


def update_track_settings(
    db: Session,
    track_id: int,
    updates: dict
):
    allowed_fields = {
        "title",
        "artist",
        "license_name",
        "license_url",
        "allowed_public_playback",
        "is_active"
    }

    unknown_fields = set(updates) - allowed_fields

    if unknown_fields:
        raise ValueError("Переданы недопустимые поля.")

    if not updates:
        raise ValueError("Не указаны поля для обновления.")

    for field in ("allowed_public_playback", "is_active"):
        if field in updates and updates[field] is None:
            raise ValueError(f"Поле {field} не может быть пустым.")

    try:
        track = get_track(db, track_id)

        if track is None:
            raise LookupError("Аудиотрек не найден.")

        for field, value in updates.items():
            if field == "title":
                if value is None or not value.strip():
                    raise ValueError(
                        "Название трека не может быть пустым."
                    )
                value = value.strip()

            elif field in (
                "artist",
                "license_name",
                "license_url"
            ):
                value = value.strip() or None if value else None

            setattr(track, field, value)

        db.commit()
        db.refresh(track)

        return track

    except Exception:
        db.rollback()
        raise
