
from app.database import SessionLocal
from app.models.recommendation import Recommendation

db = SessionLocal()

try:
    recommendations = (
        db.query(Recommendation)
        .order_by(
            Recommendation.artwork_id,
            Recommendation.score.desc()
        )
        .all()
    )

    for item in recommendations:
        print(
            f"Картина ID: {item.artwork_id} | "
            f"Рекомендация ID: {item.id} | "
            f"Трек ID: {item.track_id} | "
            f"Оценка: {item.score} | "
            f"Статус: {item.status}"
        )

finally:
    db.close()
