
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation



def create_recommendation(
    db: Session,
    artwork_id: int,
    track_id: int,
    score: float,
    algorithm_version: str
):
    recommendation = (
        db.query(Recommendation)
        .filter(
            Recommendation.artwork_id == artwork_id,
            Recommendation.track_id == track_id,
            Recommendation.algorithm_version == algorithm_version
        )
        .first()
    )

    if recommendation is not None:
        recommendation.score = score
        return recommendation

    recommendation = Recommendation(
        artwork_id=artwork_id,
        track_id=track_id,
        score=score,
        algorithm_version=algorithm_version,
        status="proposed"
    )

    db.add(recommendation)
    db.flush()

    return recommendation


def get_recommendation(db: Session, recommendation_id: int):
    return db.get(Recommendation, recommendation_id)


def get_artwork_recommendations(db: Session, artwork_id: int):
    return (
        db.query(Recommendation)
        .filter(Recommendation.artwork_id == artwork_id)
        .order_by(Recommendation.score.desc())
        .all()
    )


def update_recommendation_status(
    db: Session,
    recommendation_id: int,
    status: str,
    reviewed_by: int | None = None,
    comment: str | None = None
):
    if status not in ("approved", "rejected"):
        raise ValueError("Недопустимый статус рекомендации")

    recommendation = db.get(Recommendation, recommendation_id)

    if recommendation is None:
        return None

    try:
        if status == "approved":
            old_recommendations = (
                db.query(Recommendation)
                .filter(
                    Recommendation.artwork_id == recommendation.artwork_id,
                    Recommendation.status == "approved",
                    Recommendation.id != recommendation.id
                )
                .all()
            )

            for old_recommendation in old_recommendations:
                old_recommendation.status = "proposed"

            db.flush()

        recommendation.status = status
        recommendation.reviewed_by = reviewed_by
        recommendation.reviewed_at = datetime.now(timezone.utc)
        recommendation.comment = comment

        db.commit()
        db.refresh(recommendation)

        return recommendation

    except Exception:
        db.rollback()
        raise
