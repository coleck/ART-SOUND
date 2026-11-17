
from pathlib import Path

from app.database import SessionLocal
from app.models.artwork import Artwork
from app.services.artwork_service import add_artwork


# Путь к папке с изображениями.
PROJECT_DIR = Path(__file__).resolve().parent.parent
ARTWORKS_DIR = PROJECT_DIR / "media" / "artworks"

db = SessionLocal()

try:
    for image_path in sorted(ARTWORKS_DIR.iterdir()):

        if not image_path.is_file():
            continue

        if image_path.suffix.lower() not in (
            ".jpg", ".jpeg", ".png", ".webp"
        ):
            continue

        # Проверяем, не загружали ли файл раньше.
        existing = (
            db.query(Artwork)
            .filter(Artwork.image_path == str(image_path))
            .first()
        )

        if existing:
            print(f"Уже загружена: {image_path.name}")
            continue

        artwork = add_artwork(
        db=db,
        title=image_path.stem,
        artist="Неизвестен",
        image_path=str(image_path)
        )

        print(
            f"Добавлена картина: {artwork.title}, "
            f"ID: {artwork.id}"
        )

finally:
    db.rollback()
    db.close()
