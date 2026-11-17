
import pytest

from app.models.audio_track import AudioTrack


# ============================================================
# ТЕСТОВЫЙ МУЗЫКАЛЬНЫЙ ТРЕК
# ============================================================

@pytest.fixture
def sample_track(db_session):
    # Создаём запись только в тестовой базе.
    track = AudioTrack(
        title="Тестовый трек",
        artist="Тестовый исполнитель",
        file_path="/tmp/test-track.mp3",
        duration_sec=120,
        license_name="Старая лицензия",
        license_url="https://example.com/old-license",
        allowed_public_playback=True,
        is_active=True
    )

    db_session.add(track)
    db_session.flush()

    return track


# ============================================================
# ТЕСТЫ PATCH /tracks/{track_id}
# ============================================================

def test_update_all_track_settings(client, sample_track):
    # Изменяем все доступные настройки.
    response = client.patch(
        f"/tracks/{sample_track.id}",
        json={
            "license_name": "Новая лицензия",
            "license_url": "https://example.com/new-license",
            "allowed_public_playback": False,
            "is_active": False
        }
    )

    assert response.status_code == 200

    data = response.json()["track"]

    assert data["license_name"] == "Новая лицензия"
    assert data["license_url"] == "https://example.com/new-license"
    assert data["allowed_public_playback"] is False
    assert data["is_active"] is False


def test_partial_track_update(client, sample_track):
    # Меняем только активность.
    response = client.patch(
        f"/tracks/{sample_track.id}",
        json={
            "is_active": False
        }
    )

    assert response.status_code == 200

    data = response.json()["track"]

    # Проверяем, что остальные настройки не изменились.
    assert data["is_active"] is False
    assert data["license_name"] == "Старая лицензия"
    assert data["license_url"] == "https://example.com/old-license"
    assert data["allowed_public_playback"] is True


def test_clear_license_name(client, sample_track):
    # Проверяем возможность очистить название лицензии.
    response = client.patch(
        f"/tracks/{sample_track.id}",
        json={
            "license_name": None
        }
    )

    assert response.status_code == 200
    assert response.json()["track"]["license_name"] is None


def test_update_nonexistent_track(client):
    # Обращаемся к несуществующему треку.
    response = client.patch(
        "/tracks/999999",
        json={
            "is_active": False
        }
    )

    assert response.status_code == 404


def test_empty_update(client, sample_track):
    # Пустой запрос не должен обновлять запись.
    response = client.patch(
        f"/tracks/{sample_track.id}",
        json={}
    )

    assert response.status_code == 400


def test_null_boolean_value(client, sample_track):
    # Логическое поле не должно принимать null.
    response = client.patch(
        f"/tracks/{sample_track.id}",
        json={
            "is_active": None
        }
    )

    assert response.status_code == 400
def test_updated_track_is_returned_by_get_tracks(client, sample_track):
    # Обновляем настройки трека.
    client.patch(
        f"/tracks/{sample_track.id}",
        json={
            "license_name": "Новая лицензия",
            "allowed_public_playback": False,
            "is_active": False
        }
    )

    # Получаем список треков из базы данных.
    response = client.get("/tracks")

    assert response.status_code == 200

    # Находим нужный трек.
    tracks = response.json()

    updated_track = next(
        track for track in tracks
        if track["id"] == sample_track.id
    )

    # Проверяем сохранённые значения.
    assert updated_track["license_name"] == "Новая лицензия"
    assert updated_track["allowed_public_playback"] is False
    assert updated_track["is_active"] is False