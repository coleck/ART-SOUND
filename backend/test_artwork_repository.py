
from app.database import SessionLocal
from app.repositories.artwork_repository import (
    create_artwork,
    save_artwork_features,
    get_artwork,
    get_all_artworks
)

db = SessionLocal()
artwork = None

try:
    # 1. Создаём тестовую картину
    artwork = create_artwork(
        db=db,
        title="Тестовая картина",
        artist="Тестовый автор",
        image_path="data/artworks/test.jpg",
        description="Тест записи в базу"
    )

    print("Картина создана. ID:", artwork.id)

    # 2. Сохраняем признаки изображения
    features = {
        "brightness": 0.25,
        "contrast": 0.26,
        "saturation": 0.19,
        "edge_density": 0.09,
        "color_entropy": 0.69,
        "valence_proxy": 0.22
    }

    save_artwork_features(db, artwork.id, features)
    print("Признаки сохранены")

    # 3. Получаем картину по ID
    result = get_artwork(db, artwork.id)
    print("Получена картина:", result.title)

    # 4. Проверяем список картин
    artworks = get_all_artworks(db)
    print("Всего картин в базе:", len(artworks))

finally:
    # Удаляем тестовую запись
    if artwork is not None:
        db.delete(artwork)
        db.commit()
        print("Тестовая запись удалена")

    db.close()
