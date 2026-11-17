
from sqlalchemy.orm import Session

from app.models.artwork import Artwork
from app.models.artwork_features import ArtworkFeatures


def create_artwork(
    db: Session,
    title: str,
    artist: str,
    image_path: str,
    year: int | None = None,
    description: str | None = None,
    created_by: int | None = None
):
    artwork = Artwork(
        title=title,
        artist=artist,
        image_path=image_path,
        year=year,
        description=description,
        created_by=created_by
    )

    db.add(artwork)
    db.flush()

    return artwork


def save_artwork_features(
    db: Session,
    artwork_id: int,
    features: dict
):
    artwork_features = db.get(ArtworkFeatures, artwork_id)

    if artwork_features is None:
        artwork_features = ArtworkFeatures(
            artwork_id=artwork_id,
            **features
        )
        db.add(artwork_features)
    else:
        for key, value in features.items():
            setattr(artwork_features, key, value)

    db.flush()

    return artwork_features


def get_artwork(db: Session, artwork_id: int):
    return db.get(Artwork, artwork_id)


def get_all_artworks(db: Session):
    return db.query(Artwork).order_by(Artwork.id).all()
