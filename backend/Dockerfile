
FROM python:3.14-slim

WORKDIR /app

# Системные библиотеки для OpenCV и обработки аудио.
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsndfile1 \
    ffmpeg \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-зависимости.
COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код backend.
COPY backend/ ./backend/
COPY media/ ./media/

# Запускаем FastAPI.
WORKDIR /app/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
