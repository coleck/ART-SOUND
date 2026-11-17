
from app.database import SessionLocal
from app.repositories.recommendation_repository import (
    get_artwork_recommendations,
    update_recommendation_status
)
from app.models.recommendation import Recommendation


db = SessionLocal()

test_ids = []

try:
    artwork_id = 4

    recommendations = get_artwork_recommendations(db, artwork_id)

    if len(recommendations) < 2:
        print("Недостаточно рекомендаций для теста")

    elif any(item.status != "proposed" for item in recommendations):
        print("Тест пропущен: у картины уже есть рассмотренные рекомендации")

    else:
        first = recommendations[0]
        second = recommendations[1]

        test_ids = [first.id, second.id]

        # Одобряем первую рекомендацию.
        update_recommendation_status(
            db,
            first.id,
            "approved"
        )

        recommendations = get_artwork_recommendations(db, artwork_id)

        approved = [
            item for item in recommendations
            if item.status == "approved"
        ]

        assert len(approved) == 1
        assert approved[0].id == first.id

        print("Первое одобрение работает")

        # Одобряем вторую рекомендацию.
        update_recommendation_status(
            db,
            second.id,
            "approved"
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

        print("Автоматическая замена одобренной рекомендации работает")
        print("Все проверки пройдены")

finally:
    # Возвращаем тестовые записи в исходное состояние.
    for recommendation_id in test_ids:
        recommendation = db.get(Recommendation, recommendation_id)

        if recommendation is not None:
            recommendation.status = "proposed"
            recommendation.reviewed_by = None
            recommendation.reviewed_at = None
            recommendation.comment = None

    db.commit()
    db.close()
