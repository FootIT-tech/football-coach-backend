"""
Минималистичный бэкенд для образовательного приложения с футбольным ИИ-тренером.

Установка:  pip install fastapi uvicorn
Запуск:     uvicorn main:app --host 0.0.0.0 --port 8000
Документация (Swagger): /docs
"""

from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Football AI Coach API")

# ---------------------------------------------------------------------------
# CORS: разрешаем запросы с любого источника (Claude Artifacts, мобильное
# приложение, локальный фронтенд).
# Middleware должен быть добавлен ДО объявления эндпоинтов.
# Starlette при allow_origins=["*"] и allow_credentials=True сам подставляет
# в ответ конкретный Origin запроса (для preflight и запросов с cookie),
# так что "звёздочка" вместе с credentials не ломает preflight.
# В продакшене лучше заменить "*" на список конкретных доменов.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Схемы данных
# ---------------------------------------------------------------------------
class UserProfile(BaseModel):
    """Профиль пользователя, который отдаётся фронтенду."""
    name: str
    rank: str
    balls: int
    trophies: List[str]


class ProgressUpdate(BaseModel):
    """
    Данные прогресса от фронтенда. Все поля необязательны:
    перезаписываются только те, что были переданы.
    """
    balls: Optional[int] = Field(default=None, ge=0)
    unlocked_trophies: Optional[List[str]] = None
    rank: Optional[str] = None


# ---------------------------------------------------------------------------
# Временная "база данных" в оперативной памяти.
# Внимание: данные сбрасываются при каждом перезапуске сервера.
# ---------------------------------------------------------------------------
users_db: dict[str, dict] = {
    "demo": {
        "name": "Новичок",
        "rank": "Дебютант",
        "balls": 0,
        "trophies": [],
    }
}


def get_or_create_user(user_id: str) -> dict:
    """Возвращает пользователя; если его нет — создаёт профиль по умолчанию."""
    if user_id not in users_db:
        users_db[user_id] = {
            "name": f"Игрок {user_id}",
            "rank": "Дебютант",
            "balls": 0,
            "trophies": [],
        }
    return users_db[user_id]


# ---------------------------------------------------------------------------
# Эндпоинты
# ---------------------------------------------------------------------------
@app.get("/api/user/{user_id}", response_model=UserProfile)
def get_user(user_id: str):
    """Загрузка профиля: имя, ранг, количество ⚽ мячей, массив кубков."""
    return get_or_create_user(user_id)


@app.post("/api/user/{user_id}/progress", response_model=UserProfile)
def update_progress(user_id: str, progress: ProgressUpdate):
    """
    Обновление прогресса. Пример тела запроса:
    {"balls": 250, "unlocked_trophies": ["physics"]}
    Переданные значения ПЕРЕЗАПИСЫВАЮТ сохранённые в базе.
    """
    user = get_or_create_user(user_id)

    # exclude_unset=True — берём только поля, которые реально прислал клиент
    data = progress.model_dump(exclude_unset=True)

    if data.get("balls") is not None:
        user["balls"] = data["balls"]
    if data.get("unlocked_trophies") is not None:
        user["trophies"] = data["unlocked_trophies"]
    if data.get("rank") is not None:
        user["rank"] = data["rank"]

    return user
