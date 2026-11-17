
import pytest

from app.models.artwork import Artwork
from app.models.audio_track import AudioTrack
from app.models.recommendation import Recommendation

from app.services.artwork_service import publish_artwork


# ============================================================
# ПОДГОТОВКА ТЕСТОВЫХ ДАННЫХ
# ============================================================

@pytest.fixture
def publish_data(db_session, tmp_path):
    # Создаём временные файлы картины и аудиозаписи.
    image_path = tmp_path / "artwork.jpg"
    audio_path = tmp_path / "track.mp3"

    image_path.write_bytes(b"test image")
    audio_path.write_bytes(b"test audio")

    # Создаём картину.
    artwork = Artwork(
        title="Тестовая картина",
        artist="Тестовый художник",
        image_path=str(image_path)
    )

    # Создаём музыкальный трек.
    track = AudioTrack(
        title="Тестовый трек",
        artist="Тестовый исполнитель",
        file_path=str(audio_path),
        allowed_public_playback=True,
        is_active=True
    )

    db_session.add_all([artwork, track])
    db_session.flush()

    # Создаём одобренную рекомендацию.
    recommendation = Recommendation(
        artwork_id=artwork.id,
        track_id=track.id,
        score=95.50,
        algorithm_version="matching_v1",
        status="approved"
    )

    db_session.add(recommendation)
    db_session.flush()

    return artwork, track, recommendation


# ============================================================
# УСПЕШНАЯ ПУБЛИКАЦИЯ
# ============================================================

def test_publish_artwork_success(
    db_session,
    publish_data
):
    artwork, track, recommendation = publish_data

    # Запускаем публикацию.
    result = publish_artwork(
        db=db_session,
        artwork_id=artwork.id
    )

    assert result.status == "published"


# ============================================================
# ПРОВЕРКА ОДОБРЕННОЙ РЕКОМЕНДАЦИИ
# ============================================================

def test_publish_without_approved_recommendation(
    db_session,
    publish_data
):
    artwork, track, recommendation = publish_data

    # Меняем статус рекомендации.
    recommendation.status = "proposed"
    db_session.flush()

    with pytest.raises(ValueError):
        publish_artwork(
            db=db_session,
            artwork_id=artwork.id
        )


# ============================================================
# ПРОВЕРКА АКТИВНОСТИ ТРЕКА
# ============================================================

def test_publish_with_inactive_track(
    db_session,
    publish_data
):
    artwork, track, recommendation = publish_data

    # Отключаем музыкальный трек.
    track.is_active = False
    db_session.flush()

    with pytest.raises(ValueError):
        publish_artwork(
            db=db_session,
            artwork_id=artwork.id
        )


# ============================================================
# ПРОВЕРКА РАЗРЕШЕНИЯ НА ПУБЛИЧНОЕ ВОСПРОИЗВЕДЕНИЕ
# ============================================================

def test_publish_without_public_playback_permission(
    db_session,
    publish_data
):
    artwork, track, recommendation = publish_data

    # Запрещаем публичное воспроизведение.
    track.allowed_public_playback = False
    db_session.flush()

    with pytest.raises(ValueError):
        publish_artwork(
            db=db_session,
            artwork_id=artwork.id
        )


# ============================================================
# ПРОВЕРКА НАЛИЧИЯ ФАЙЛА КАРТИНЫ
# ============================================================

def test_publish_without_image_file(
    db_session,
    publish_data
):
    artwork, track, recommendation = publish_data

    # Удаляем временный файл изображения.
    from pathlib import Path
    Path(artwork.image_path).unlink()

    with pytest.raises(ValueError):
        publish_artwork(
            db=db_session,
            artwork_id=artwork.id
        )


# ============================================================
# ПРОВЕРКА НАЛИЧИЯ АУДИОФАЙЛА
# ============================================================

def test_publish_without_audio_file(
    db_session,
    publish_data
):
    artwork, track, recommendation = publish_data

    # Удаляем временный аудиофайл.
    from pathlib import Path
    Path(track.file_path).unlink()

    with pytest.raises(ValueError):
        publish_artwork(
            db=db_session,
            artwork_id=artwork.id
        )


# ============================================================
# ПРОВЕРКА НЕСУЩЕСТВУЮЩЕЙ КАРТИНЫ
# ============================================================

def test_publish_nonexistent_artwork(db_session):
    with pytest.raises(ValueError):
        publish_artwork(
            db=db_session,
            artwork_id=999999
        )
