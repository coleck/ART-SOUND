
import csv
import json

from pathlib import Path

from app.analysis.scoring.scoring import (
    build_artwork_profile,
    build_track_profile,
    calculate_score
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CACHE_DIR = PROJECT_ROOT / "data" / "analysis_cache"

ARTWORK_CACHE = CACHE_DIR / "artworks.json"
TRACK_CACHE = CACHE_DIR / "tracks.json"

RESULTS_DIR = PROJECT_ROOT / "results"

RESULTS_FILE = RESULTS_DIR / "recommendations.csv"


def load_json(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Кэш не найден: {path}"
        )

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():

    artwork_cache = load_json(ARTWORK_CACHE)
    track_cache = load_json(TRACK_CACHE)

    artworks = artwork_cache.get("artworks", {})
    tracks = track_cache.get("tracks", {})

    if not artworks:
        raise ValueError("Нет проанализированных картин")

    if not tracks:
        raise ValueError("Нет проанализированных треков")

    results = []

    print(f"Картин в каталоге: {len(artworks)}")
    print(f"Треков в каталоге: {len(tracks)}")

    # Перебираем каждую картину.
    for artwork_path, artwork_data in artworks.items():

        artwork_file = PROJECT_ROOT / artwork_path

        if not artwork_file.exists():
            print(f"Пропускаем отсутствующую картину: {artwork_path}")
            continue

        artwork_features = artwork_data["features"]

        artwork_profile = build_artwork_profile(
            artwork_features
        )

        artwork_results = []

        # Сравниваем картину со всеми треками.
        for track_path, track_data in tracks.items():

            track_file = PROJECT_ROOT / track_path

            if not track_file.exists():
                continue

            track_features = track_data["features"]

            track_profile = build_track_profile(
                track_features
            )

            result = calculate_score(
                artwork_profile,
                track_profile
            )

            row = {
                "artwork": artwork_file.name,
                "artwork_path": artwork_path,
                "track": track_file.name,
                "track_path": track_path,
                "score": result["score"],
                "distance": result["distance"],
                "estimated_mode": track_features.get(
                    "estimated_mode", "unknown"
                ),
                "mode_confidence": track_features.get(
                    "mode_confidence", 0
                ),
                "differences": json.dumps(
                    result["differences"],
                    ensure_ascii=False
                )
            }

            artwork_results.append(row)

        # Сортировка от лучшего трека к худшему.
        artwork_results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        results.extend(artwork_results)

        print("\n===================================")
        print(f"КАРТИНА: {artwork_file.name}")
        print("===================================")

        for position, item in enumerate(
            artwork_results[:5],
            start=1
        ):

            print(
                f"{position}. {item['track']} "
                f"| Score: {item['score']} "
                f"| Лад: {item['estimated_mode']}"
            )

    if not results:
        raise RuntimeError(
            "Не удалось сформировать рекомендации"
        )

    # Сохраняем общую таблицу результатов.
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = [
        "artwork",
        "artwork_path",
        "track",
        "track_path",
        "score",
        "distance",
        "estimated_mode",
        "mode_confidence",
        "differences"
    ]

    with open(
        RESULTS_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

    print("\n========== ИТОГО ==========")
    print(f"Рассчитано пар: {len(results)}")
    print(f"Результаты: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
