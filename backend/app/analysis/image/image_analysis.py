
from pathlib import Path

import cv2
import numpy as np


def analyze_image(image_path: str) -> dict:
    """
    Автоматически извлекает визуальные признаки картины
    и рассчитывает предварительную оценку эмоциональной окраски.
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Изображение не найдено: {path}")

    image = cv2.imread(str(path))

    if image is None:
        raise ValueError("Не удалось открыть изображение")

    # Уменьшаем слишком большие изображения.
    height, width = image.shape[:2]
    max_size = 1200

    if max(height, width) > max_size:
        scale = max_size / max(height, width)

        image = cv2.resize(
            image,
            (int(width * scale), int(height * scale))
        )

    # Преобразуем изображение.
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 1. Средняя светлота.
    brightness = float(np.mean(lab[:, :, 0]) / 255)

    # 2. Контрастность.
    contrast = float(np.std(gray) / 128)

    # 3. Насыщенность.
    saturation = float(np.mean(hsv[:, :, 1]) / 255)

    # 4. Плотность контуров.
    edges = cv2.Canny(gray, 100, 200)
    edge_density = float(np.mean(edges > 0))

    # 5. Разнообразие цветовой палитры.
    histogram = cv2.calcHist(
        [hsv],
        [0, 1],
        None,
        [16, 16],
        [0, 180, 0, 256]
    )

    probabilities = histogram.flatten()
    probabilities = probabilities / (probabilities.sum() + 1e-10)

    nonzero = probabilities[probabilities > 0]

    entropy = -np.sum(nonzero * np.log2(nonzero))
    max_entropy = np.log2(len(probabilities))

    color_entropy = float(entropy / max_entropy)

    # 6. Автоматическая оценка эмоциональной окраски.
    # Более светлые и насыщенные изображения
    # получают более высокую оценку.
    valence_proxy = (
        0.5 * brightness +
        0.5 * saturation
    )

    valence_proxy = float(np.clip(valence_proxy, 0, 1))

    return {
        "brightness": round(brightness, 4),
        "contrast": round(contrast, 4),
        "saturation": round(saturation, 4),
        "edge_density": round(edge_density, 4),
        "color_entropy": round(color_entropy, 4),
        "valence_proxy": round(valence_proxy, 4)
    }
