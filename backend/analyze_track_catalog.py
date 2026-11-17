
import argparse
import json

from datetime import datetime, timezone
from pathlib import Path

from app.analysis.audio.audio_analysis import analyze_audio


# Корневая папка проекта.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Папка с музыкой.
TRACKS_DIR = PROJECT_ROOT / "media" / "tracks"

# Файл с результатами анализа.
CACHE_FILE = (
    PROJECT_ROOT
    / "data"
    / "analysis_cache"
    / "tracks.json"
)

# Форматы аудио.
AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".flac",
    ".ogg"
}

# Меняем версию, если изменяем сам алгоритм анализа аудио.
ANALYZER_VERSION = "audio_v1"


def load_cache():
    """Загружает предыдущие результаты анализа."""

    if not CACHE_FILE.exists():
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        print("Не удалось прочитать кэш. Создаём новый.")
        return {}


def save_cache(cache):
    """Безопасно сохраняет результаты анализа."""

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
    """
    Получает характеристики файла для проверки изменений.
    """

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
        help="Повторно проанализировать все треки"
    )

    args = parser.parse_args()

    if not TRACKS_DIR.exists():
        raise FileNotFoundError(
            f"Папка с музыкой не найдена: {TRACKS_DIR}"
        )

    old_cache = load_cache()

    # Если версия анализа изменилась,
    # старые результаты больше не используем.
    if old_cache.get("analyzer_version") != ANALYZER_VERSION:
        print("Версия анализатора изменилась. Создаём новый кэш.")
        old_tracks = {}
    else:
        old_tracks = old_cache.get("tracks", {})

    track_files = sorted([
        file
        for file in TRACKS_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() in AUDIO_EXTENSIONS
    ])

    if not track_files:
        print("Музыкальный каталог пуст.")
        return

    new_tracks = {}

    analyzed_count = 0
    cached_count = 0
    error_count = 0

    print(f"Найдено аудиофайлов: {len(track_files)}")

    for index, track_path in enumerate(track_files, start=1):

        relative_path = track_path.relative_to(
            PROJECT_ROOT
        ).as_posix()

        fingerprint = get_fingerprint(track_path)

        previous = old_tracks.get(relative_path)

        # Проверяем, можно ли использовать старый результат.
        if (
            not args.force
            and previous is not None
            and previous.get("fingerprint") == fingerprint
            and previous.get("features") is not None
        ):

            new_tracks[relative_path] = previous

            cached_count += 1

            print(
                f"[{index}/{len(track_files)}] "
                f"Используем кэш: {track_path.name}"
            )

            continue

        # Если файла нет в кэше или он изменился,
        # выполняем новый анализ.
        print(
            f"[{index}/{len(track_files)}] "
            f"Анализируем: {track_path.name}"
        )

        try:

            features = analyze_audio(str(track_path))

            new_tracks[relative_path] = {
                "fingerprint": fingerprint,
                "features": features
            }

            analyzed_count += 1

        except Exception as error:

            print(
                f"Ошибка анализа {track_path.name}: {error}"
            )

            error_count += 1

    # Формируем новый кэш.
    # Удалённые из каталога файлы автоматически исчезнут из кэша.
    cache = {
        "cache_version": 1,
        "analyzer_version": ANALYZER_VERSION,
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "tracks": new_tracks
    }

    save_cache(cache)

    print("\n========== РЕЗУЛЬТАТ ==========")
    print(f"Всего файлов: {len(track_files)}")
    print(f"Проанализировано заново: {analyzed_count}")
    print(f"Взято из кэша: {cached_count}")
    print(f"Ошибок: {error_count}")
    print(f"Кэш сохранён: {CACHE_FILE}")


if __name__ == "__main__":
    main()
