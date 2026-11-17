
def clip01(value: float) -> float:
    """Ограничивает значение диапазоном 0..1."""
    return max(0.0, min(1.0, float(value)))


def normalize(
    value: float,
    min_value: float,
    max_value: float
) -> float:
    """Нормализует значение в диапазон 0..1."""

    if max_value <= min_value:
        raise ValueError("Неверные границы нормализации")

    result = (value - min_value) / (max_value - min_value)

    return clip01(result)


def build_artwork_profile(features: dict) -> dict:
    """
    Создаёт профиль картины из автоматически
    извлечённых визуальных характеристик.
    """

    valence = clip01(features["valence_proxy"])

    contrast = clip01(features["contrast"])
    saturation = clip01(features["saturation"])

    edge = normalize(
        features["edge_density"],
        0,
        0.25
    )

    color_entropy = clip01(features["color_entropy"])

    # Оценка визуальной энергичности.
    energy = (
        0.45 * contrast +
        0.30 * edge +
        0.25 * saturation
    )

    # Оценка визуальной текстуры.
    texture = (
        0.60 * edge +
        0.40 * color_entropy
    )

    return {
        "valence": round(valence, 4),
        "energy": round(clip01(energy), 4),
        "texture": round(clip01(texture), 4),
        "brightness": round(
            clip01(features["brightness"]), 4
        )
    }


def build_track_profile(features: dict) -> dict:
    """
    Создаёт профиль музыкального трека из автоматически
    извлечённых характеристик.
    """

    valence = clip01(features["valence_proxy"])

    # Нормализация музыкальных показателей.
    bpm = normalize(
        features["tempo_bpm"],
        50,
        180
    )

    rms_change = normalize(
        features["rms_std"],
        0,
        0.20
    )

    onset = normalize(
        features["onset_rate"],
        0,
        8
    )

    spectral_contrast = normalize(
        features["spectral_contrast_mean"],
        0,
        40
    )

    mfcc_variability = normalize(
        features["mfcc_std"],
        0,
        30
    )

    spectral_brightness = normalize(
        features["spectral_centroid_mean"],
        0,
        5000
    )

    # Оценка музыкальной энергичности.
    energy = (
        0.40 * bpm +
        0.30 * rms_change +
        0.30 * onset
    )

    # Оценка музыкальной текстуры.
    texture = (
        0.55 * spectral_contrast +
        0.45 * mfcc_variability
    )

    return {
        "valence": round(valence, 4),
        "energy": round(clip01(energy), 4),
        "texture": round(clip01(texture), 4),
        "brightness": round(
            spectral_brightness, 4
        )
    }


# Веса критериев.
WEIGHTS = {
    "valence": 0.40,
    "energy": 0.30,
    "texture": 0.20,
    "brightness": 0.10
}


def calculate_score(
    artwork_profile: dict,
    track_profile: dict
) -> dict:
    """
    Рассчитывает совместимость картины и музыкального трека.

    Score находится в диапазоне 0..100.
    """

    differences = {}

    for feature in WEIGHTS:

        if feature not in artwork_profile:
            raise ValueError(
                f"В профиле картины отсутствует {feature}"
            )

        if feature not in track_profile:
            raise ValueError(
                f"В профиле музыки отсутствует {feature}"
            )

        differences[feature] = abs(
            artwork_profile[feature] -
            track_profile[feature]
        )

    distance = sum(
        WEIGHTS[feature] * differences[feature]
        for feature in WEIGHTS
    )

    score = 100 * (1 - distance)

    return {
        "score": round(score, 2),
        "distance": round(distance, 4),
        "differences": {
            key: round(value, 4)
            for key, value in differences.items()
        }
    }
