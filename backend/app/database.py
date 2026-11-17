
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Определяем корневую папку проекта.
BASE_DIR = Path(__file__).resolve().parents[2]

# Загружаем настройки из .env.
load_dotenv(BASE_DIR / ".env")

import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в файле .env")


# Создаём подключение к PostgreSQL.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# Фабрика сессий для работы с базой.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


# Базовый класс для моделей таблиц.
class Base(DeclarativeBase):
    pass


# Зависимость для получения сессии в API.
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
