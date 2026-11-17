
import os
from pathlib import Path

import pytest

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


# ============================================================
# НАСТРОЙКА ТЕСТОВОЙ БАЗЫ ДАННЫХ
# ============================================================

# Корневая папка проекта.
PROJECT_DIR = Path(__file__).resolve().parents[2]

# Загружаем настройки основного проекта.
load_dotenv(PROJECT_DIR / ".env")

# Получаем адрес PostgreSQL.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден.")

# Формируем адрес отдельной тестовой базы.
database_url = make_url(DATABASE_URL)

TEST_DATABASE_NAME = "picture_sound_test"

if not database_url.database:
    raise RuntimeError("В DATABASE_URL не указано имя базы данных.")

# Заменяем имя базы, сохраняя остальные параметры подключения.
test_database_url = database_url.set(
    database=TEST_DATABASE_NAME
)

# Проверяем, что тесты не могут обратиться к другой базе.
if test_database_url.database != TEST_DATABASE_NAME:
    raise RuntimeError("Неверная тестовая база данных.")

# Важно: устанавливаем адрес до импорта приложения.
os.environ["DATABASE_URL"] = test_database_url.render_as_string(
    hide_password=False
)


# ============================================================
# ПОДКЛЮЧЕНИЕ К ТЕСТОВОЙ БАЗЕ
# ============================================================

from app.database import Base, engine, get_db

# Регистрируем модели SQLAlchemy.
from app.models.artwork import Artwork
from app.models.artwork_features import ArtworkFeatures
from app.models.audio_track import AudioTrack
from app.models.recommendation import Recommendation
from app.models.track_features import TrackFeatures
from app.models.user import User

# Проверяем фактическую базу подключения.
if engine.url.database != TEST_DATABASE_NAME:
    raise RuntimeError(
        "Тесты остановлены: подключение не к picture_sound_test."
    )


# ============================================================
# ПОДГОТОВКА ТАБЛИЦ
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    # Создаём таблицы только в тестовой базе.
    Base.metadata.create_all(bind=engine)

    yield

    # Таблицы не удаляем: тестовая база остаётся отдельной.
    # Данные каждого теста будут отменены через rollback.


# ============================================================
# ТЕСТОВАЯ СЕССИЯ
# ============================================================

@pytest.fixture
def db_session():
    # Создаём отдельное соединение.
    connection = engine.connect()

    # Начинаем внешнюю транзакцию.
    transaction = connection.begin()

    # Внутренние commit() будут работать через SAVEPOINT.
    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint"
    )

    db = TestingSessionLocal()

    try:
        yield db

    finally:
        # Закрываем сессию и отменяем внешнюю транзакцию.
        db.close()
        transaction.rollback()
        connection.close()


# ============================================================
# ТЕСТОВЫЙ КЛИЕНТ FASTAPI
# ============================================================

@pytest.fixture
def client(db_session):
    from fastapi.testclient import TestClient
    from app.main import app

    # Подменяем подключение API на тестовую сессию.
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client

    finally:
        # Удаляем переопределение после каждого теста.
        app.dependency_overrides.clear()
