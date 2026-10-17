# Билет № 2 — Интернет-магазин книг

Веб-приложение на **FastAPI + PostgreSQL**, упакованное в Docker и запускаемое через docker-compose.
Можно смотреть каталог книг, открыть карточку книги, оформить заказ, посмотреть список заказов и отдельный заказ.

## Быстрый старт

```bash
docker compose up --build
```

Затем открыть:

- http://localhost:8000 — сайт (каталог)
- http://localhost:8000/docs — Swagger UI (автодокументация API)

Остановить: `docker compose down` (с удалением данных БД: `docker compose down -v`).

При первом запуске таблицы создаются автоматически, а в каталог добавляются 5 демо-книг.

---

## Шаг 1. Проектирование

### База данных

```
books                         orders
─────────────────────         ──────────────────────────────
id      SERIAL PK      ◄──┐   id          SERIAL PK
title   VARCHAR(255)      └── book_id     INT FK → books.id
price   NUMERIC(10,2) >0      quantity    INT > 0
stock   INT >= 0              created_at  TIMESTAMPTZ DEFAULT now()
```

Связь **один-ко-многим**: у одной книги может быть много заказов, каждый заказ ссылается ровно на одну книгу.
`ON DELETE RESTRICT` не даёт удалить книгу, по которой есть заказы.
Ограничения `price > 0`, `quantity > 0` продублированы и в БД (CHECK), и в Pydantic (`Field(gt=0)`).

### Страницы (HTML, шаблоны Jinja2)

| № | Страница            | Метод и URL                |
|---|---------------------|----------------------------|
| 1 | Каталог             | `GET /`                    |
| 2 | Карточка книги      | `GET /books/{id}`          |
| 3 | Список заказов      | `GET /orders`              |
| 4 | Страница заказа     | `GET /orders/{id}`         |
| 5 | Оформление заказа   | `GET /orders/new`, `POST /orders/new` |

### REST API (JSON)

| Метод | URL                  | Описание                    |
|-------|----------------------|-----------------------------|
| GET   | `/api/books`         | список книг                 |
| GET   | `/api/books/{id}`    | одна книга                  |
| POST  | `/api/books`         | добавить книгу (price > 0)  |
| GET   | `/api/orders`        | список заказов              |
| GET   | `/api/orders/{id}`   | один заказ                  |
| POST  | `/api/orders`        | создать заказ (quantity > 0)|
| GET   | `/health`            | проверка работоспособности  |

Пример:

```bash
curl -X POST http://localhost:8000/api/orders -H "Content-Type: application/json" -d '{"book_id": 1, "quantity": 2}'
curl -X POST http://localhost:8000/api/books  -H "Content-Type: application/json" -d '{"title": "Тест", "price": -5, "stock": 1}'   # → 422, price должен быть > 0
```

## Шаг 2. Приложение

```
app/
├── main.py        # создание FastAPI, роуты HTML-страниц и JSON API
├── database.py    # подключение к PostgreSQL (SQLAlchemy engine, сессии)
├── models.py      # ORM-модели Book и Order (таблицы books, orders)
├── schemas.py     # Pydantic-схемы с валидацией Field(gt=0)
├── crud.py        # функции работы с БД (чтение, создание заказа с проверкой склада)
├── seed.py        # демо-данные
└── templates/     # Jinja2-шаблоны 5 страниц + base.html
```

При оформлении заказа остаток книги на складе уменьшается; строка книги блокируется (`SELECT ... FOR UPDATE`),
чтобы два одновременных заказа не продали больше, чем есть.

## Шаг 3. Docker

- **Dockerfile** — образ на `python:3.12-slim`, зависимости ставятся отдельным слоем (кэш), запуск `uvicorn` от непривилегированного пользователя.
- **docker-compose.yml** — два сервиса:
  - `db` — `postgres:16-alpine`, данные в volume `pgdata`, **healthcheck** через `pg_isready`;
  - `web` — собирается из Dockerfile, `depends_on: db: condition: service_healthy` — приложение стартует только после того, как БД реально готова принимать подключения.
- Строка подключения передаётся через переменную окружения `DATABASE_URL`, хост `db` — имя сервиса во внутренней сети compose.

### Выкладка в Git

```bash
git init
git add .
git commit -m "Интернет-магазин книг: FastAPI + PostgreSQL + Docker"
git remote add origin https://github.com/<user>/bookshop.git
git push -u origin main
```

## Используемые технологии

| Библиотека         | Зачем                                                    |
|--------------------|----------------------------------------------------------|
| FastAPI            | веб-фреймворк: роуты, DI (`Depends`), Swagger на `/docs` |
| Uvicorn            | ASGI-сервер, который запускает приложение                |
| SQLAlchemy 2.0     | ORM: описание таблиц классами, запросы к БД              |
| psycopg2           | драйвер PostgreSQL для Python                            |
| Pydantic           | валидация входных данных (`Field(gt=0)`)                 |
| Jinja2             | HTML-шаблоны страниц                                     |
| python-multipart   | приём данных HTML-формы (`Form(...)`)                    |
| PostgreSQL 16      | СУБД                                                     |
| Docker / Compose   | контейнеризация и запуск web + db одной командой         |
