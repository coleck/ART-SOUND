
from app.database import SessionLocal
from app.models.audio_track import AudioTrack

db = SessionLocal()

try:
    tracks = db.query(AudioTrack).order_by(AudioTrack.id).all()

    print("Всего треков:", len(tracks))

    for track in tracks:
        print(
            f"ID: {track.id} | "
            f"Название: {track.title} | "
            f"Длительность: {track.duration_sec} сек. | "
            f"Признаки: {'есть' if track.features else 'нет'}"
        )

finally:
    db.close()
