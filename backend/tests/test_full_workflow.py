
from app.services.artwork_service import (
    add_artwork,
    publish_artwork
)
from app.services.track_service import add_track
from app.services.recommendation_service import (
    generate_recommendations,
    review_recommendation,
    get_public_artwork
)


def test_full_artwork_music_workflow(
    db_session,
    monkeypatch,
    tmp_path
):
    # Подменяем анализ изображения
    def fake_analyze_image(image_path):
        return {
            "brightness": 0.6,
            "contrast": 0.5,
            "saturation": 0.7,
            "edge_density": 0.4,
            "color_entropy": 0.6,
            "valence_proxy": 0.7
        }

    # Подменяем анализ аудио
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
        "app.services.artwork_service.analyze_image",
        fake_analyze_image
    )

    monkeypatch.setattr(
        "app.services.track_service.analyze_audio",
        fake_analyze_audio
    )

    # Создаём временные файлы
    image_file = tmp_path / "artwork.jpg"
    image_file.write_bytes(b"test image")

    audio_file = tmp_path / "track.mp3"
    audio_file.write_bytes(b"test audio")

    # 1. Добавляем картину
    artwork = add_artwork(
        db=db_session,
        title="Тестовая картина",
        artist="Тестовый художник",
        image_path=str(image_file),
        year=2026,
        description="Картина для интеграционного теста"
    )

    assert artwork.id is not None
    assert artwork.features is not None

    # 2. Добавляем музыкальный трек
    track = add_track(
        db=db_session,
        title="Тестовая музыка",
        file_path=str(audio_file),
        artist="Тестовый исполнитель",
        allowed_public_playback=True
    )

    assert track.id is not None
    assert track.features is not None
    assert track.duration_sec == 180

    # 3. Генерируем рекомендации
    recommendations = generate_recommendations(
        db=db_session,
        artwork_id=artwork.id
    )

    assert len(recommendations) == 1

    recommendation = recommendations[0]

    assert recommendation.artwork_id == artwork.id
    assert recommendation.track_id == track.id
    assert recommendation.status == "proposed"
    assert 0 <= float(recommendation.score) <= 100

    # 4. Одобряем рекомендацию
    approved = review_recommendation(
        db=db_session,
        recommendation_id=recommendation.id,
        status="approved"
    )

    assert approved.status == "approved"

    # 5. Публикуем картину
    published = publish_artwork(
        db=db_session,
        artwork_id=artwork.id
    )

    assert published.status == "published"

    # 6. Получаем картину по QR-токену
    public_artwork, public_recommendation = get_public_artwork(
        db=db_session,
        qr_token=artwork.qr_token
    )

    assert public_artwork.id == artwork.id
    assert public_artwork.status == "published"

    assert public_recommendation.id == recommendation.id
    assert public_recommendation.status == "approved"
    assert public_recommendation.track.id == track.id
