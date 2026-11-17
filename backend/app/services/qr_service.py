
import os
import qrcode
from pathlib import Path


# Папка для сохранения QR-кодов.
BASE_DIR = Path(__file__).resolve().parents[2]
QR_DIR = BASE_DIR / "media" / "qr_codes"

# Адрес frontend задаётся через .env.
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
).rstrip("/")


def generate_qr_code(qr_token: str) -> str:
    # Создаём папку, если её ещё нет.
    QR_DIR.mkdir(parents=True, exist_ok=True)

    # Формируем ссылку на публичную страницу картины.
    url = f"{FRONTEND_URL}/?token={qr_token}"

    # Создаём QR-код.
    qr = qrcode.make(url)

    # Сохраняем изображение.
    file_path = QR_DIR / f"{qr_token}.png"
    qr.save(file_path)

    return str(file_path)
