
from pathlib import Path

from app.database import SessionLocal
from app.services.track_service import add_track
from app.models.audio_track import AudioTrack


# Определяем путь к папке с аудиофайлами.
PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACKS_DIR = PROJECT_DIR / "media" / "tracks"


db = SessionLocal()

try:
    for track_path in sorted(TRACKS_DIR.iterdir()):

        if not track_path.is_file():
            continue

        if track_path.suffix.lower() not in (".mp3", ".wav", ".flac", ".ogg"):
            continue

        # Проверяем, загружен ли трек ранее.
        existing = (
            db.query(AudioTrack)
            .filter(AudioTrack.file_path == str(track_path))
            .first()
        )

        if existing:
            print(f"Уже загружен: {track_path.name}")
            continue

        # Добавляем трек и анализируем его.
        track = add_track(
            db=db,
            title=track_path.stem,
            file_path=str(track_path),
            artist="Неизвестен",
            allowed_public_playback=False
        )

        print(f"Добавлен трек: {track.title}, ID: {track.id}")

finally:
    db.rollback()
    db.close()
