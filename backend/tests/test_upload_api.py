
from types import SimpleNamespace

from app import main


# ============================================================
# ТЕСТЫ ЗАГРУЗКИ МУЗЫКАЛЬНЫХ ТРЕКОВ
# ============================================================

def test_upload_track_success(client, monkeypatch, tmp_path):
    # Переносим загрузку во временную папку.
    tracks_dir = tmp_path / "tracks"
    monkeypatch.setattr(main, "TRACKS_DIR", tracks_dir)

    # Подменяем анализ аудио.
    def fake_add_track(**kwargs):
        return SimpleNamespace(
            id=101,
            title=kwargs["title"],
            artist=kwargs["artist"],
            duration_sec=120,
            allowed_public_playback=kwargs["allowed_public_playback"],
            is_active=True
        )

    monkeypatch.setattr(main, "add_track", fake_add_track)

    # Отправляем тестовый файл.
    response = client.post(
        "/tracks",
        data={
            "title": "Тестовый трек",
            "artist": "Тестовый исполнитель",
            "allowed_public_playback": "false"
        },
        files={
            "audio": ("test.mp3", b"fake audio data", "audio/mpeg")
        }
    )

    assert response.status_code == 200

    data = response.json()["track"]

    assert data["title"] == "Тестовый трек"
    assert data["duration_sec"] == 120
    assert data["allowed_public_playback"] is False

    # Проверяем сохранение файла во временной папке.
    uploaded_files = list(tracks_dir.iterdir())

    assert len(uploaded_files) == 1
    assert uploaded_files[0].read_bytes() == b"fake audio data"


def test_upload_track_invalid_format(client):
    # Проверяем запрет неподдерживаемого формата.
    response = client.post(
        "/tracks",
        data={"title": "Тест"},
        files={
            "audio": ("test.txt", b"some data", "text/plain")
        }
    )

    assert response.status_code == 400


def test_upload_track_empty_file(client):
    # Проверяем запрет пустого аудиофайла.
    response = client.post(
        "/tracks",
        data={"title": "Тест"},
        files={
            "audio": ("test.mp3", b"", "audio/mpeg")
        }
    )

    assert response.status_code == 400


# ============================================================
# ТЕСТЫ ЗАГРУЗКИ КАРТИН
# ============================================================

def test_upload_artwork_success(client, monkeypatch, tmp_path):
    # Используем временную папку для изображений.
    artworks_dir = tmp_path / "artworks"
    monkeypatch.setattr(main, "ARTWORKS_DIR", artworks_dir)

    # Подменяем создание картины и анализ изображения.
    def fake_add_artwork(**kwargs):
        return SimpleNamespace(
            id=201,
            title=kwargs["title"],
            artist=kwargs["artist"],
            year=kwargs["year"],
            description=kwargs["description"],
            status="draft"
        )

    monkeypatch.setattr(main, "add_artwork", fake_add_artwork)

    # Отправляем тестовое изображение.
    response = client.post(
        "/artworks",
        data={
            "title": "Тестовая картина",
            "artist": "Тестовый художник",
            "year": 2026,
            "description": "Описание картины"
        },
        files={
            "image": ("test.jpg", b"fake image data", "image/jpeg")
        }
    )

    assert response.status_code == 200

    data = response.json()["artwork"]

    assert data["title"] == "Тестовая картина"
    assert data["artist"] == "Тестовый художник"
    assert data["status"] == "draft"

    # Проверяем сохранение файла во временной папке.
    uploaded_files = list(artworks_dir.iterdir())

    assert len(uploaded_files) == 1
    assert uploaded_files[0].read_bytes() == b"fake image data"


def test_upload_artwork_invalid_format(client):
    # Проверяем запрет неподдерживаемого формата.
    response = client.post(
        "/artworks",
        data={
            "title": "Тестовая картина",
            "artist": "Тестовый художник"
        },
        files={
            "image": ("test.txt", b"some data", "text/plain")
        }
    )

    assert response.status_code == 400
