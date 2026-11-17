 
import argparse
import json

from datetime import datetime, timezone
from pathlib import Path

from app.analysis.image.image_analysis import analyze_image


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ARTWORKS_DIR = PROJECT_ROOT / "media" / "artworks"

CACHE_FILE = (
    PROJECT_ROOT
    / "data"
    / "analysis_cache"
    / "artworks.json"
)

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

ANALYZER_VERSION = "image_v1"


def load_cache():

    if not CACHE_FILE.exists():
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        print("Не удалось прочитать кэш.")
        return {}


def save_cache(cache):

    CACHE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_file = CACHE_FILE.with_suffix(".tmp")

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(
            cache,
            file,
            indent=4,
            ensure_ascii=False
        )

    temporary_file.replace(CACHE_FILE)


def get_fingerprint(file_path):

    stat = file_path.stat()

    return {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns
    }


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--force",
        action="store_true",
        help="Повторно проанализировать все картины"
    )

    args = parser.parse_args()

    if not ARTWORKS_DIR.exists():
        raise FileNotFoundError(
            f"Папка с картинами не найдена: {ARTWORKS_DIR}"
        )

    old_cache = load_cache()

    if old_cache.get("analyzer_version") != ANALYZER_VERSION:
        old_artworks = {}
    else:
        old_artworks = old_cache.get("artworks", {})

    image_files = sorted([
        file
        for file in ARTWORKS_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() in IMAGE_EXTENSIONS
    ])

    if not image_files:
        print("Каталог изображений пуст.")
        return

    new_artworks = {}

    analyzed_count = 0
    cached_count = 0
    error_count = 0

    print(f"Найдено изображений: {len(image_files)}")

    for index, image_path in enumerate(image_files, start=1):

        relative_path = image_path.relative_to(
            PROJECT_ROOT
        ).as_posix()

        fingerprint = get_fingerprint(image_path)

        previous = old_artworks.get(relative_path)

        if (
            not args.force
            and previous is not None
            and previous.get("fingerprint") == fingerprint
            and previous.get("features") is not None
        ):

            new_artworks[relative_path] = previous

            cached_count += 1

            print(
                f"[{index}/{len(image_files)}] "
                f"Используем кэш: {image_path.name}"
            )

            continue

        print(
            f"[{index}/{len(image_files)}] "
            f"Анализируем: {image_path.name}"
        )

        try:

            features = analyze_image(str(image_path))

            new_artworks[relative_path] = {
                "fingerprint": fingerprint,
                "features": features
            }

            analyzed_count += 1

        except Exception as error:

            print(
                f"Ошибка анализа {image_path.name}: {error}"
            )

            error_count += 1

    cache = {
        "cache_version": 1,
        "analyzer_version": ANALYZER_VERSION,
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "artworks": new_artworks
    }

    save_cache(cache)

    print("\n========== РЕЗУЛЬТАТ ==========")
    print(f"Всего изображений: {len(image_files)}")
    print(f"Проанализировано заново: {analyzed_count}")
    print(f"Взято из кэша: {cached_count}")
    print(f"Ошибок: {error_count}")
    print(f"Кэш сохранён: {CACHE_FILE}")


if __name__ == "__main__":
    main()
