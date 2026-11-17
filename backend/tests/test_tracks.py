
from app.models.audio_track import AudioTrack
from app.models.track_features import TrackFeatures
from app.services.track_service import add_track


def test_add_track_saves_track_and_features(
    db_session,
    monkeypatch,
    tmp_path
):
    # Подменяем анализ аудио тестовыми данными
    def fake_analyze_audio(file_path):
        return {
            "duration_sec": 180,
            "tempo_bpm": 120.0,
            "rms_mean": 0.15,
            "rms_std": 0.05,
            "spectral_centroid_mean": 1500.0,
            "onset_rate": 2.0,
            "spectral_contrast_mean": 20.0,
            "mfcc_std": 5.0,
            "estimated_mode": "major",
            "mode_difference": 1.0,
            "mode_confidence": 0.8,
            "valence_proxy": 0.7
        }

    monkeypatch.setattr(
        "app.services.track_service.analyze_audio",
        fake_analyze_audio
    )

    # Создаём временный аудиофайл
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"test audio")

    # Добавляем трек через сервис
    track = add_track(
        db=db_session,
        title="Тестовый трек",
        file_path=str(audio_file),
        artist="Тестовый исполнитель",
        duration_sec=180
    )

    # Проверяем сохранение трека
    saved_track = db_session.get(AudioTrack, track.id)

    assert saved_track is not None
    assert saved_track.title == "Тестовый трек"
    assert saved_track.artist == "Тестовый исполнитель"
    assert saved_track.duration_sec == 180

    # Проверяем сохранение признаков аудио
    saved_features = db_session.get(TrackFeatures, track.id)

    assert saved_features is not None
    assert saved_features.tempo_bpm == 120.0
    assert saved_features.valence_proxy == 0.7
