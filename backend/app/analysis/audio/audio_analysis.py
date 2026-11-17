
from pathlib import Path

import librosa
import numpy as np


# Эталонные профили Krumhansl–Kessler.
# Порядок нот: C, C#, D, D#, E, F, F#, G, G#, A, A#, B.

MAJOR_PROFILE = np.array([
    6.35, 2.23, 3.48, 2.33,
    4.38, 4.09, 2.52, 5.19,
    2.39, 3.66, 2.29, 2.88
])

MINOR_PROFILE = np.array([
    6.33, 2.68, 3.52, 5.38,
    2.60, 3.53, 2.54, 4.75,
    3.98, 2.69, 3.34, 3.17
])


def calculate_correlation(first, second):
    """Вычисляет корреляцию двух профилей."""

    if np.std(first) < 1e-10 or np.std(second) < 1e-10:
        return 0.0

    result = np.corrcoef(first, second)[0, 1]

    if not np.isfinite(result):
        return 0.0

    return float(result)


def estimate_musical_valence(y, sr):
    """
    Оценивает относительное преобладание мажорного
    или минорного характера музыки.

    Использует распределение chroma и эталонные
    профили мажорных и минорных тональностей.
    """

    hop_length = 512

    chroma = librosa.feature.chroma_stft(
        y=y,
        sr=sr,
        hop_length=hop_length
    )

    # Разбиваем аудио на окна примерно по 3 секунды.
    frames_per_window = int(3 * sr / hop_length)

    mode_differences = []

    for start in range(
        0,
        chroma.shape[1],
        frames_per_window
    ):

        segment = chroma[
            :,
            start:start + frames_per_window
        ]

        # Слишком короткие фрагменты не учитываем.
        if segment.shape[1] < frames_per_window // 2:
            continue

        # Усреднённое распределение энергии по нотам.
        chroma_profile = np.mean(segment, axis=1)

        major_scores = []
        minor_scores = []

        # Проверяем все 12 мажорных и 12 минорных тональностей.
        for shift in range(12):

            major_key = np.roll(MAJOR_PROFILE, shift)
            minor_key = np.roll(MINOR_PROFILE, shift)

            major_scores.append(
                calculate_correlation(
                    chroma_profile,
                    major_key
                )
            )

            minor_scores.append(
                calculate_correlation(
                    chroma_profile,
                    minor_key
                )
            )

        # Наилучшее соответствие каждого типа.
        best_major = max(major_scores)
        best_minor = max(minor_scores)

        # Положительное значение указывает
        # на преобладание мажорных профилей.
        mode_difference = best_major - best_minor

        mode_differences.append(mode_difference)

    if not mode_differences:
        return {
            "estimated_mode": "unclear",
            "mode_difference": 0.0,
            "mode_confidence": 0.0,
            "valence_proxy": 0.5
        }

    average_difference = float(np.mean(mode_differences))

    # Преобразуем разницу в диапазон -1..1.
    # Коэффициент 5 — начальная настройка чувствительности.
    relative_mode = float(np.tanh(5 * average_difference))

    # Нейтральное значение — 0.5.
    # Мажорное направление повышает оценку,
    # минорное — снижает.
    valence_proxy = 0.5 + 0.25 * relative_mode

    # Определяем примерное направление.
    if average_difference > 0.02:
        estimated_mode = "major"
    elif average_difference < -0.02:
        estimated_mode = "minor"
    else:
        estimated_mode = "unclear"

    return {
        "estimated_mode": estimated_mode,
        "mode_difference": round(average_difference, 5),
        "mode_confidence": round(abs(relative_mode), 4),
        "valence_proxy": round(valence_proxy, 4)
    }


def analyze_audio(audio_path: str) -> dict:
    """
    Извлекает характеристики аудио
    и автоматически определяет его эмоциональную окраску.
    """

    path = Path(audio_path)

    if not path.exists():
        raise FileNotFoundError(f"Аудио не найдено: {path}")

    # Загружаем аудио.
    y, sr = librosa.load(
        path,
        sr=None,
        mono=True
    )

    if len(y) == 0:
        raise ValueError("Аудиофайл пустой")

    duration = len(y) / sr

    if duration < 1:
        raise ValueError("Аудиофайл слишком короткий")

    # 1. Темп.
    tempo, beats = librosa.beat.beat_track(
        y=y,
        sr=sr
    )

    tempo_bpm = float(np.asarray(tempo).reshape(-1)[0])

    # 2. RMS — энергия сигнала.
    rms = librosa.feature.rms(y=y)[0]

    rms_mean = float(np.mean(rms))
    rms_std = float(np.std(rms))

    # 3. Спектральный центроид.
    centroid = librosa.feature.spectral_centroid(
        y=y,
        sr=sr
    )[0]

    centroid_mean = float(np.mean(centroid))

    # 4. Частота звуковых событий.
    onset_times = librosa.onset.onset_detect(
        y=y,
        sr=sr,
        units="time"
    )

    onset_rate = float(len(onset_times) / duration)

    # 5. Спектральный контраст.
    spectral_contrast = librosa.feature.spectral_contrast(
        y=y,
        sr=sr
    )

    spectral_contrast_mean = float(
        np.mean(spectral_contrast)
    )

    # 6. MFCC.
    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=13
    )

    mfcc_std = float(
        np.mean(np.std(mfcc, axis=1))
    )

    # 7. Автоматическая оценка эмоциональной окраски.
    mood_features = estimate_musical_valence(y, sr)

    return {
        "duration_sec": round(duration, 2),
        "tempo_bpm": round(tempo_bpm, 2),
        "rms_mean": round(rms_mean, 5),
        "rms_std": round(rms_std, 5),
        "spectral_centroid_mean": round(
            centroid_mean, 2
        ),
        "onset_rate": round(onset_rate, 4),
        "spectral_contrast_mean": round(
            spectral_contrast_mean, 4
        ),
        "mfcc_std": round(mfcc_std, 4),
        **mood_features
    }
