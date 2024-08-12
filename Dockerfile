# Используем базовый образ Python
FROM python:3.12.2

COPY poetry.lock pyproject.toml ./

RUN python -m pip install --no-cache-dir poetry==1.4.2 \
    && poetry config virtualenvs.create false \
    && poetry install --without dev,tests --no-interaction --no-ansi \
    && rm -rf $(poetry config cache-dir)/{cache,artifacts}

WORKDIR /app

# Копируем исходный код приложения внутрь контейнера
COPY . /app

# Команда для запуска приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
