
from types import SimpleNamespace

from app import main


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ТЕСТОВЫЕ ОБЪЕКТЫ
# ============================================================

def create_recommendation():
    track = SimpleNamespace(
        id=10,
        title="Тестовый трек",
        artist="Тестовый исполнитель",
        duration_sec=120
    )

    return SimpleNamespace(
        id=50,
        artwork_id=1,
        track_id=10,
        track=track,
        score=93.5,
        status="proposed",
        algorithm_version="matching_v1"
    )


def create_artwork():
    return SimpleNamespace(
        id=1,
        title="Тестовая картина",
        artist="Тестовый художник",
        year=2026,
        description="Тестовое описание",
        status="published"
    )


# ============================================================
# ГЕНЕРАЦИЯ РЕКОМЕНДАЦИЙ
# ============================================================

def test_generate_recommendations_success(client, monkeypatch):
    # Подменяем проверку существования картины.
    monkeypatch.setattr(
        main,
        "get_artwork",
        lambda db, artwork_id: create_artwork()
    )

    # Подменяем алгоритм генерации.
    monkeypatch.setattr(
        main,
        "generate_recommendations",
        lambda db, artwork_id: [create_recommendation()]
    )

    response = client.post(
        "/artworks/1/recommendations/generate"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == 50
    assert data[0]["track"]["id"] == 10
    assert data[0]["score"] == 93.5
    assert data[0]["status"] == "proposed"


def test_generate_recommendations_artwork_not_found(
    client,
    monkeypatch
):
    # Картина отсутствует в базе.
    monkeypatch.setattr(
        main,
        "get_artwork",
        lambda db, artwork_id: None
    )

    response = client.post(
        "/artworks/999/recommendations/generate"
    )

    assert response.status_code == 404


# ============================================================
# ОДОБРЕНИЕ И ОТКЛОНЕНИЕ РЕКОМЕНДАЦИЙ
# ============================================================

def test_approve_recommendation(client, monkeypatch):
    recommendation = create_recommendation()
    recommendation.status = "approved"

    # Подменяем функцию одобрения.
    monkeypatch.setattr(
        main,
        "review_recommendation",
        lambda **kwargs: recommendation
    )

    response = client.post(
        "/recommendations/50/approve",
        json={
            "comment": "Подходит для картины"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 50
    assert data["status"] == "approved"
    assert data["artwork_id"] == 1
    assert data["track_id"] == 10


def test_reject_recommendation(client, monkeypatch):
    recommendation = create_recommendation()
    recommendation.status = "rejected"

    # Подменяем функцию отклонения.
    monkeypatch.setattr(
        main,
        "review_recommendation",
        lambda **kwargs: recommendation
    )

    response = client.post(
        "/recommendations/50/reject",
        json={
            "comment": "Не подходит"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 50
    assert data["status"] == "rejected"


def test_review_nonexistent_recommendation(
    client,
    monkeypatch
):
    # Имитируем отсутствие рекомендации.
    def fake_review(**kwargs):
        raise ValueError("Рекомендация не найдена.")

    monkeypatch.setattr(
        main,
        "review_recommendation",
        fake_review
    )

    response = client.post(
        "/recommendations/999/approve",
        json={}
    )

    assert response.status_code == 404


# ============================================================
# ПУБЛИЧНАЯ СТРАНИЦА КАРТИНЫ
# ============================================================

def test_public_artwork_success(client, monkeypatch):
    artwork = create_artwork()
    recommendation = create_recommendation()
    recommendation.status = "approved"

    # Подменяем получение опубликованной картины.
    monkeypatch.setattr(
        main,
        "get_public_artwork",
        lambda db, qr_token: (artwork, recommendation)
    )

    response = client.get(
        "/public/artworks/test-token"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["artwork"]["id"] == 1
    assert data["artwork"]["title"] == "Тестовая картина"
    assert data["music"]["id"] == 10
    assert data["music"]["title"] == "Тестовый трек"
    assert data["music"]["score"] == 93.5


def test_public_artwork_not_available(
    client,
    monkeypatch
):
    # Имитируем невозможность получить публичную картину.
    def fake_get_public_artwork(**kwargs):
        raise ValueError("Картина не опубликована.")

    monkeypatch.setattr(
        main,
        "get_public_artwork",
        fake_get_public_artwork
    )

    response = client.get(
        "/public/artworks/unknown-token"
    )

    assert response.status_code == 404


# ============================================================
# ПУБЛИКАЦИЯ КАРТИНЫ
# ============================================================

def test_publish_artwork_success(client, monkeypatch):
    artwork = create_artwork()

    # Подменяем сервис публикации.
    monkeypatch.setattr(
        main,
        "publish_artwork",
        lambda db, artwork_id: artwork
    )

    response = client.post(
        "/artworks/1/publish"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["artwork_id"] == 1
    assert data["status"] == "published"


def test_publish_artwork_without_approval(
    client,
    monkeypatch
):
    # Имитируем отсутствие одобренной рекомендации.
    def fake_publish_artwork(db, artwork_id):
        raise ValueError(
            "Для картины нет одобренной музыкальной композиции."
        )

    monkeypatch.setattr(
        main,
        "publish_artwork",
        fake_publish_artwork
    )

    response = client.post(
        "/artworks/1/publish"
    )

    assert response.status_code == 400
