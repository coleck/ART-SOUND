from pathlib import Path
import json

from app.analysis.image.image_analysis import analyze_image
from app.analysis.audio.audio_analysis import analyze_audio
from app.analysis.scoring.scoring import (
    build_artwork_profile,
    build_track_profile,
    calculate_score
)


# Определяем корневую папку проекта.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Указываем тестовые файлы.
IMAGE_PATH = PROJECT_ROOT / "media/artworks/test.jpg"
AUDIO_PATH = PROJECT_ROOT / "media/tracks/test.mp3"


def main():

    if not IMAGE_PATH.exists():
        print(f"Изображение не найдено: {IMAGE_PATH}")
        return

    if not AUDIO_PATH.exists():
        print(f"Аудио не найдено: {AUDIO_PATH}")
        return

    # Анализируем картину.
    image_features = analyze_image(str(IMAGE_PATH))

    # Анализируем музыкальный файл.
    audio_features = analyze_audio(str(AUDIO_PATH))

    # Создаём профили автоматически.
    artwork_profile = build_artwork_profile(
    image_features
)

    track_profile = build_track_profile(
    audio_features
)

# Рассчитываем совместимость.
    result = calculate_score(
    artwork_profile,
    track_profile
)
    

    print("\n========== АНАЛИЗ КАРТИНЫ ==========")
    print(json.dumps(image_features, indent=4, ensure_ascii=False))

    print("\n========== АНАЛИЗ МУЗЫКИ ==========")
    print(json.dumps(audio_features, indent=4, ensure_ascii=False))

    print("\n========== РЕЗУЛЬТАТ ==========")
    print(json.dumps(result, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()