
import pytest

from app.models.artwork import Artwork
from app.models.artwork_features import ArtworkFeatures
from app.models.audio_track import AudioTrack
from app.models.track_features import TrackFeatures
from app.models.recommendation import Recommendation

from app.services.recommendation_service import (
    generate_recommendations,
    review_recommendation
)


def create_artwork(db, with_features=True):
    artwork = Artwork(
        title="Тестовая картина",
        artist="Тестовый художник",
        image_path="test.jpg"
    )

    db.add(artwork)
    db.flush()

    if with_features:
        features = ArtworkFeatures(
            artwork_id=artwork.id,
            brightness=0.6,
            contrast=0.5,
            saturation=0.7,
            edge_density=0.4,
            color_entropy=0.6,
            valence_proxy=0.5
        )

        db.add(features)
        db.flush()

    return artwork


def create_track(db, title, is_active=True, with_features=True):
    track = AudioTrack(
        title=title,
        artist="Тестовый исполнитель",
        file_path="test.mp3",
        duration_sec=180,
        is_active=is_active
    )

    db.add(track)
    db.flush()

    if with_features:
        features = TrackFeatures(
            track_id=track.id,
            tempo_bpm=120,
            rms_mean=0.3,
            rms_std=0.2,
            spectral_centroid_mean=2000,
            onset_rate=2.0,
            spectral_contrast_mean=20,
            mfcc_std=10,
            estimated_mode="major",
            mode_difference=0.2,
            mode_confidence=0.8,
            valence_proxy=0.5
        )

        db.add(features)
        db.flush()

    return track


def test_generate_recommendations(db_session):
    artwork = create_artwork(db_session)

    active_track = create_track(
        db_session,
        "Активный трек"
    )

    create_track(
        db_session,
        "Неактивный трек",
        is_active=False
    )

    create_track(
        db_session,
        "Трек без признаков",
        with_features=False
    )

    db_session.flush()

    recommendations = generate_recommendations(
        db_session,
        artwork.id
    )

    assert len(recommendations) == 1

    recommendation = recommendations[0]

    assert recommendation.artwork_id == artwork.id
    assert recommendation.track_id == active_track.id
    assert recommendation.status == "proposed"
    assert 0 <= float(recommendation.score) <= 100


def test_generate_recommendations_without_duplicates(db_session):
    artwork = create_artwork(db_session)
    track = create_track(db_session, "Тестовый трек")

    db_session.flush()

    first_result = generate_recommendations(
        db_session,
        artwork.id
    )

    first_id = first_result[0].id

    second_result = generate_recommendations(
        db_session,
        artwork.id
    )

    assert len(first_result) == 1
    assert len(second_result) == 1
    assert second_result[0].id == first_id

    count = (
        db_session.query(Recommendation)
        .filter(
            Recommendation.artwork_id == artwork.id,
            Recommendation.track_id == track.id,
            Recommendation.algorithm_version == "matching_v1"
        )
        .count()
    )

    assert count == 1


def test_generate_recommendations_without_artwork_features(db_session):
    artwork = create_artwork(
        db_session,
        with_features=False
    )

    with pytest.raises(ValueError, match="отсутствуют признаки"):
        generate_recommendations(
            db_session,
            artwork.id
        )


def test_generate_recommendations_for_missing_artwork(db_session):
    with pytest.raises(ValueError, match="не найдена"):
        generate_recommendations(
            db_session,
            999999
        )

def test_approve_recommendation(db_session):
    artwork = create_artwork(db_session)
    track = create_track(db_session, "Трек для одобрения")

    recommendation = Recommendation(
        artwork_id=artwork.id,
        track_id=track.id,
        score=85.0,
        algorithm_version="matching_v1",
        status="proposed"
    )

    db_session.add(recommendation)
    db_session.flush()

    result = review_recommendation(
        db=db_session,
        recommendation_id=recommendation.id,
        status="approved",
        comment="Подходит для картины"
    )

    assert result.status == "approved"
    assert result.comment == "Подходит для картины"
    assert result.reviewed_at is not None


def test_approve_new_recommendation_replaces_old(db_session):
    artwork = create_artwork(db_session)

    first_track = create_track(db_session, "Первый трек")
    second_track = create_track(db_session, "Второй трек")

    first_recommendation = Recommendation(
        artwork_id=artwork.id,
        track_id=first_track.id,
        score=80.0,
        algorithm_version="matching_v1",
        status="approved"
    )

    second_recommendation = Recommendation(
        artwork_id=artwork.id,
        track_id=second_track.id,
        score=90.0,
        algorithm_version="matching_v1",
        status="proposed"
    )

    db_session.add_all([
        first_recommendation,
        second_recommendation
    ])
    db_session.flush()

    review_recommendation(
        db=db_session,
        recommendation_id=second_recommendation.id,
        status="approved"
    )

    db_session.refresh(first_recommendation)
    db_session.refresh(second_recommendation)

    assert first_recommendation.status == "proposed"
    assert second_recommendation.status == "approved"


def test_reject_recommendation(db_session):
    artwork = create_artwork(db_session)
    track = create_track(db_session, "Отклоняемый трек")

    recommendation = Recommendation(
        artwork_id=artwork.id,
        track_id=track.id,
        score=50.0,
        algorithm_version="matching_v1",
        status="proposed"
    )

    db_session.add(recommendation)
    db_session.flush()

    result = review_recommendation(
        db=db_session,
        recommendation_id=recommendation.id,
        status="rejected",
        comment="Не подходит"
    )

    assert result.status == "rejected"
    assert result.comment == "Не подходит"


def test_review_invalid_status(db_session):
    with pytest.raises(ValueError, match="Недопустимый статус"):
        review_recommendation(
            db=db_session,
            recommendation_id=1,
            status="unknown"
        )


def test_review_missing_recommendation(db_session):
    with pytest.raises(ValueError, match="не найдена"):
        review_recommendation(
            db=db_session,
            recommendation_id=999999,
            status="approved"
        )
