# Выбор backend-фреймворка: FastAPI vs PHP vs Node.js

**Дата извлечения**: 2026-05-16
**Источник**: 2026-04-22/6e4ca94c-сравнение-fastapi-и-php.md
**Раздел**: decisions

## Суть
Сравнение архитектурных подходов для разработчика, переходящего с PHP+HTML на Python+FastAPI. FastAPI — асинхронный фреймворк для API (JSON), в отличие от PHP-монолита с генерацией HTML.

## Ключевые отличия FastAPI от PHP

| Аспект | PHP + HTML | FastAPI |
|--------|-----------|---------|
| Роутинг | Физический путь к файлу (`/user.php`) | Декораторы (`@app.get("/user/{id}")`) |
| Получение данных | `$_GET`, `$_POST`, ручная фильтрация | Автоматический парсинг + Pydantic-валидация |
| Ответ | `echo "<h1>HTML</h1>"` | `return {"json": "data"}` |
| БД | Синхронные вызовы | async/await (неблокирующие) |
| Процесс | Перезагрузка на каждый запрос | Один процесс, высокая скорость |
| Шаблоны | PHP в HTML | Jinja2 (автоэкранирование) |

## Структура проекта FastAPI
```
app/
├── main.py          # точка входа
├── routers/         # роутеры (контроллеры)
├── models/          # Pydantic-схемы
├── crud.py          # работа с БД
└── database.py      # подключение к БД
```

## Связи
- Связано с: adnd-knowledge/decisions/css-framework-choice.md
- Связано с: adnd-knowledge/decisions/database-choice.md
- Связано с: adnd-knowledge/api-spec/deepseek-chat-vs-api.md