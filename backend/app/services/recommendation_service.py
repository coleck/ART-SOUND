
from sqlalchemy.orm import Session

from app.models.artwork import Artwork
from app.models.audio_track import AudioTrack
from app.models.recommendation import Recommendation

from app.analysis.scoring.scoring import (
    build_artwork_profile,
    build_track_profile,
    calculate_score
)

from app.repositories.recommendation_repository import (
    create_recommendation,
    get_artwork_recommendations,
    get_recommendation,
    update_recommendation_status
)


def generate_recommendations(
    db: Session,
    artwork_id: int
):
    try:
        # Получаем картину из базы.
        artwork = db.get(Artwork, artwork_id)

        if artwork is None:
            raise ValueError("Картина не найдена")

        if artwork.features is None:
            raise ValueError("У картины отсутствуют признаки")

        # Формируем профиль картины.
        artwork_features = {
            "brightness": artwork.features.brightness,
            "contrast": artwork.features.contrast,
            "saturation": artwork.features.saturation,
            "edge_density": artwork.features.edge_density,
            "color_entropy": artwork.features.color_entropy,
            "valence_proxy": artwork.features.valence_proxy
        }

        artwork_profile = build_artwork_profile(artwork_features)

        # Получаем активные музыкальные треки.
        tracks = (
            db.query(AudioTrack)
            .filter(AudioTrack.is_active == True)
            .all()
        )

        # Рассчитываем совместимость каждого трека.
        for track in tracks:

            if track.features is None:
                continue

            track_features = {
                "tempo_bpm": track.features.tempo_bpm,
                "rms_std": track.features.rms_std,
                "onset_rate": track.features.onset_rate,
                "spectral_contrast_mean": track.features.spectral_contrast_mean,
                "mfcc_std": track.features.mfcc_std,
                "spectral_centroid_mean": track.features.spectral_centroid_mean,
                "valence_proxy": track.features.valence_proxy
            }

            track_profile = build_track_profile(track_features)

            result = calculate_score(
                artwork_profile,
                track_profile
            )

            # Сохраняем или обновляем рекомендацию.
            create_recommendation(
                db=db,
                artwork_id=artwork.id,
                track_id=track.id,
                score=result["score"],
                algorithm_version="matching_v1"
            )

        # Сохраняем все изменения.
        db.commit()

        # Возвращаем рекомендации картины.
        return get_artwork_recommendations(
            db=db,
            artwork_id=artwork.id
        )

    except Exception:
        db.rollback()
        raise

def review_recommendation(
    db: Session,
    recommendation_id: int,
    status: str,
    reviewed_by=None,
    comment=None
):
    # Проверяем допустимый статус.
    if status not in ("approved", "rejected"):
        raise ValueError("Недопустимый статус рекомендации")

    # Проверяем, существует ли рекомендация.
    recommendation = get_recommendation(db, recommendation_id)

    if recommendation is None:
        raise ValueError("Рекомендация не найдена")

    # Передаём изменение статуса в репозиторий.
    return update_recommendation_status(
        db=db,
        recommendation_id=recommendation_id,
        status=status,
        reviewed_by=reviewed_by,
        comment=comment
    )
    
def get_recommendations_for_artwork(
    db: Session,
    artwork_id: int
):
    # Проверяем существование картины.
    artwork = db.get(Artwork, artwork_id)

    if artwork is None:
        raise ValueError("Картина не найдена")

    # Получаем рекомендации из базы.
    return get_artwork_recommendations(
        db=db,
        artwork_id=artwork_id
    )
    

def get_public_artwork(db: Session, qr_token: str):
    # Ищем картину по QR-токену.
    artwork = (
        db.query(Artwork)
        .filter(Artwork.qr_token == qr_token)
        .first()
    )

    if artwork is None:
        raise ValueError("Картина не найдена")

    # Проверяем, опубликована ли картина.
    if artwork.status != "published":
        raise ValueError("Картина пока не опубликована")

    # Получаем одобренную рекомендацию.
    recommendation = (
        db.query(Recommendation)
        .filter(
            Recommendation.artwork_id == artwork.id,
            Recommendation.status == "approved"
        )
        .first()
    )

    if recommendation is None:
        raise ValueError("Для картины пока нет одобренной музыки")

    track = recommendation.track

    # Проверяем возможность публичного воспроизведения.
    if not track.is_active:
        raise ValueError("Музыкальный трек неактивен")

    if not track.allowed_public_playback:
        raise ValueError("Публичное воспроизведение трека не разрешено")

    return artwork, recommendation
