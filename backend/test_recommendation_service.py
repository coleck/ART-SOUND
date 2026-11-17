
from app.database import SessionLocal
from app.models.recommendation import Recommendation
from app.repositories.recommendation_repository import (
    get_artwork_recommendations
)
from app.services.recommendation_service import review_recommendation


db = SessionLocal()

test_ids = []

try:
    artwork_id = 4

    recommendations = get_artwork_recommendations(db, artwork_id)

    proposed = [
        item for item in recommendations
        if item.status == "proposed"
    ]

    if len(proposed) < 2:
        print("Недостаточно рекомендаций для теста")

    else:
        first = proposed[0]
        second = proposed[1]

        test_ids = [first.id, second.id]

        # Одобряем первую рекомендацию через сервис.
        review_recommendation(
            db,
            first.id,
            "approved",
            comment="Тестовое одобрение"
        )

        print("Первая рекомендация одобрена через сервис")

        # Одобряем вторую рекомендацию.
        review_recommendation(
            db,
            second.id,
            "approved",
            comment="Тестовая замена"
        )

        recommendations = get_artwork_recommendations(db, artwork_id)

        approved = [
            item for item in recommendations
            if item.status == "approved"
        ]

        assert len(approved) == 1
        assert approved[0].id == second.id

        first = db.get(Recommendation, first.id)
        assert first.status == "proposed"

        print("Автоматическая замена работает через сервис")
        print("Все проверки пройдены")

finally:
    # Восстанавливаем исходные статусы тестовых записей.
    for recommendation_id in test_ids:
        item = db.get(Recommendation, recommendation_id)

        if item is not None:
            item.status = "proposed"
            item.reviewed_by = None
            item.reviewed_at = None
            item.comment = None

    db.commit()
    db.close()
