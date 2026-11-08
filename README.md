# Habit Tracker API

Трекер привычек на стеке: Django, DRF, Celery + Redis, PostgreSQL, Docker.

**Прод:** http://158.160.205.203
**Swagger:** http://158.160.205.203/api/docs/

## Стек

- **Backend:** Django 5 + Django REST Framework
- **API Docs:** drf-spectacular (Swagger UI + OpenAPI schema)
- **DB:** PostgreSQL 16 (persistent volume)
- **Broker:** Redis 7
- **Background Tasks:** Celery + Celery Beat (напоминания в Telegram)
- **Web Server:** Gunicorn (в контейнере web) + Nginx (reverse proxy)
- **Контейнеры:** Docker Compose
- **CI/CD:** GitHub Actions (автодеплой на сервер)

## Структура сервисов (docker-compose)

| Сервис   | Назначение                       | Порты         |
| :------- | :------------------------------- | :------------ |
| `web`    | Django + DRF + Gunicorn          | 8000 (внутр.) |
| `nginx`  | Reverse proxy, раздача статики   | 80 (наружу)   |
| `db`     | PostgreSQL (данные в volume)     | 5432 (внутр.) |
| `redis`  | Брокер сообщений Celery          | 6379 (внутр.) |
| `worker` | Выполнение фоновых задач         | —             |
| `beat`   | Планировщик периодических задач  | —             |

Наружу открыты только порты **80** (веб) и **22** (SSH).

## Как запустить проект

1. Склонируйте репозиторий:

   ```bash
   git clone https://github.com/fess88888/habit-tracker.git
   cd habit-tracker
   ```

2. Создайте файл `.env` на основе `.env.example`:

   ```env
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=localhost,127.0.0.1
   DB_NAME=habit_db
   DB_USER=habit_user
   DB_PASSWORD=strong-password
   DB_HOST=db
   DB_PORT=5432
   REDIS_URL=redis://redis:6379/0
   CELERY_BROKER_URL=redis://redis:6379/0
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   ```

   > Для продакшена добавьте в `ALLOWED_HOSTS` внешний IP сервера.

3. Соберите и запустите контейнеры:

   ```bash
   docker compose build
   docker compose up -d
   ```

4. Проверьте, что все шесть сервисов поднялись:

   ```bash
   docker compose ps
   ```

   Миграции и сбор статики выполняются автоматически при старте контейнера `web`.

## Артефакты для проверки (для наставника)

### 1. API отвечает через Nginx

```bash
curl http://localhost/api/habits/
```

Ожидаемый ответ: `{"detail":"Authentication credentials were not provided."}` —
запрос прошёл через Nginx → web → Django, DRF корректно требует авторизацию.

### 2. Swagger и OpenAPI схема

- Swagger UI: `http://localhost/api/docs/`
- OpenAPI JSON: `http://localhost/api/schema/`

Схема генерируется автоматически через `drf-spectacular`.

### 3. Celery, Redis и фоновые задачи

```bash
docker compose exec worker celery -A habit_tracker report
```

В выводе должно быть `transport: redis`, `results: redis://...` — соединение с Redis подтверждено.

Задача `send_telegram_reminder` настроена в админке Django Celery Beat.
Аргументы не передаются — задача сама выбирает активные привычки.

### 4. Миграции применены

```bash
docker compose exec web python manage.py showmigrations
```

Все миграции должны быть отмечены как `[X]` (применены).

### 5. Статика

Статика собирается автоматически при старте `web` и раздаётся через Nginx
из volume `static_volume`.

## Тестирование

Проект покрыт юнит-тестами (`tracker/tests.py`), которые проверяют:

- Получение списка привычек с учётом пагинации DRF (`LimitOffsetPagination`).
- Создание новой привычки через API.
- Соблюдение бизнес-правил модели `Habit` (валидация в `clean()`).

**Особенности тестов:**

- Учтена пагинация DRF: ответ API парсится через `data['results']`,
  чтобы корректно получить список объектов.
- Соблюдены ограничения модели: в тестах не передаются конфликтующие поля
  (например, `reward` и `related_habit` одновременно), чтобы не вызывать
  `ValidationError` на этапе создания тестовых данных.
- Обязательные поля (например, `time_of_day`) всегда передаются при создании привычки.

**Запуск тестов:**

```bash
docker compose exec web python manage.py test
```

## Деплой на сервер (Yandex Cloud)

Сервер: ВМ на Yandex Cloud, Ubuntu 24.04, Docker + Docker Compose.
Код живёт в `/var/www/habit-tracker`, ветка `develop`.

Деплой автоматизирован через GitHub Actions:

1. В репозитории (Settings → Secrets and variables → Actions) заданы секреты:
   `SSH_HOST`, `SSH_USER`, `SSH_KEY`.
2. При пуше/мерже в ветку `develop` workflow подключается к серверу по SSH,
   подтягивает код (`git pull origin develop`) и пересобирает стек
   (`docker compose up -d --build`).

Ручной деплой (если нужно проверить вручную):

```bash
cd /var/www/habit-tracker
git pull origin develop
docker compose up -d --build
docker compose ps
```

## Безопасность

- `DEBUG=False` в продакшене.
- `ALLOWED_HOSTS` ограничен конкретными хостами/IP.
- `.env` не попадает в git (добавлен в `.gitignore`).
- Статика отдаётся через Nginx, а не через Django.
- Наружу открыты только порты 80 и 22.
- Контейнеры используют минимальные образы (alpine).

## Полезные команды

| Действие                   | Команда                                                            |
| :------------------------- | :----------------------------------------------------------------- |
| Логи web                   | `docker compose logs -f web`                                       |
| Логи beat                  | `docker compose logs -f beat`                                      |
| Перезапустить весь стек    | `docker compose restart`                                           |
| Пересобрать и поднять      | `docker compose up -d --build`                                     |
| Остановить стек            | `docker compose down`                                              |
| Shell в web                | `docker compose exec web sh`                                       |
| Проверить миграции         | `docker compose exec web python manage.py showmigrations`          |
| Применить миграции вручную | `docker compose exec web python manage.py migrate`                 |
| Собрать статику вручную    | `docker compose exec web python manage.py collectstatic --noinput` |
