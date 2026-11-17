
from sqlalchemy.orm import Session

from app.models.audio_track import AudioTrack
from app.models.track_features import TrackFeatures


def create_track(
    db: Session,
    title: str,
    file_path: str,
    artist: str | None = None,
    duration_sec: int | None = None,
    license_name: str | None = None,
    license_url: str | None = None,
    allowed_public_playback: bool = False,
    created_by: int | None = None
):
    track = AudioTrack(
        title=title,
        artist=artist,
        file_path=file_path,
        duration_sec=duration_sec,
        license_name=license_name,
        license_url=license_url,
        allowed_public_playback=allowed_public_playback,
        created_by=created_by
    )

    db.add(track)
    db.flush()

    return track


def save_track_features(
    db: Session,
    track_id: int,
    features: dict
):
    features = features.copy()
    features.pop("duration_sec", None)

    track_features = db.get(TrackFeatures, track_id)

    if track_features is None:
        track_features = TrackFeatures(
            track_id=track_id,
            **features
        )
        db.add(track_features)
    else:
        for key, value in features.items():
            setattr(track_features, key, value)

    db.flush()

    return track_features


def get_track(db: Session, track_id: int):
    return db.get(AudioTrack, track_id)


def get_all_tracks(db: Session):
    return db.query(AudioTrack).order_by(AudioTrack.id).all()
