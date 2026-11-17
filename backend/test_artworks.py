
from app.database import SessionLocal
from app.models.artwork import Artwork

db = SessionLocal()

try:
    artworks = db.query(Artwork).order_by(Artwork.id).all()

    print("Всего картин:", len(artworks))

    for artwork in artworks:
        print(
            f"ID: {artwork.id} | "
            f"Название: {artwork.title} | "
            f"Признаки: {'есть' if artwork.features else 'нет'}"
        )

finally:
    db.close()
