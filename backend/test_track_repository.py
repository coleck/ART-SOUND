
from app.database import SessionLocal
from app.repositories.track_repository import (
    create_track,
    save_track_features,
    get_track,
    get_all_tracks
)

db = SessionLocal()
track = None

try:
    # 1. Создаём тестовый трек
    track = create_track(
        db=db,
        title="Тестовый трек",
        artist="Тестовый исполнитель",
        file_path="data/music/test.mp3",
        duration_sec=190
    )

    print("Трек создан. ID:", track.id)

    # 2. Сохраняем признаки аудио
    features = {
        "tempo_bpm": 114.8,
        "rms_mean": 0.258,
        "rms_std": 0.122,
        "spectral_centroid_mean": 1165.87,
        "onset_rate": 5.12,
        "spectral_contrast_mean": 21.56,
        "mfcc_std": 23.01,
        "estimated_mode": "minor",
        "mode_difference": -0.084,
        "mode_confidence": 0.4,
        "valence_proxy": 0.4
    }

    save_track_features(db, track.id, features)
    print("Признаки сохранены")

    # 3. Получаем трек по ID
    result = get_track(db, track.id)
    print("Получен трек:", result.title)

    # 4. Получаем все треки
    tracks = get_all_tracks(db)
    print("Всего треков в базе:", len(tracks))

finally:
    # Удаляем тестовую запись
    if track is not None:
        db.delete(track)
        db.commit()
        print("Тестовая запись удалена")

    db.close()
