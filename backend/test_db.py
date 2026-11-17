
from sqlalchemy import text

from app.database import engine


try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user")
        )

        database_name, username = result.fetchone()

        print("Подключение успешно!")
        print(f"База данных: {database_name}")
        print(f"Пользователь: {username}")

except Exception as error:
    print("Ошибка подключения к PostgreSQL:")
    print(error)
