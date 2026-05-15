# Prompt: Создание структуры базы знаний ADND

Сгенерировано: 2026-05-15 16:09
На основе плана: `project_memory/plans/2026-05-15_adnd-knowledge-structure.md`

---

<role>
DevOps-инженер / разработчик, работающий с файловой структурой проекта на VPS под управлением Linux.
</role>

<task>
Создать структуру директорий и файлов для AI-читаемой базы знаний ADND (`/opt/lind/adnd-knowledge/`) — 12 папок с README.md заглушками согласно утверждённому плану.
</task>

<context>
Проект: ADND — настольная ролевая игра с AI-мастером (Dungeon Master на базе LLM).

Исходные данные:
- Исходные чаты DeepSeek (115 чатов, 8.1 MB) уже распарсены в `/opt/lind/chat_deepseek/`
- План утверждён в `/opt/lind/project_memory/plans/2026-05-15_adnd-knowledge-structure.md`
- Структура согласована с пользователем (вариант A: папки для каждой темы, без числовых префиксов, README.md в каждой папке)

Текущий VPS-пользователь: `exis`. Git-репозиторий: `/opt/lind/` (branch: main, remote: origin).

Необходимо создать следующую структуру в `/opt/lind/adnd-knowledge/`:

```
adnd-knowledge/
├── README.md                   # Точка входа: карта, стратегия чтения для AI, ссылки на все разделы
├── vision/
│   └── README.md               # Идея, философия, Древо Миров, Бог-Узник, Завет Молчания
├── game-design/
│   └── README.md               # Механики: d20, 6 атрибутов, магия=химия, Книги, Стражи, beyond
├── system-prompts/
│   ├── README.md               # Объяснение архитектуры промтов
│   ├── exis-master.md          # Системный промт Экс-Ис (Бог-Узник)
│   ├── anima-assistant.md      # Системный промт Анимы (искра души)
│   ├── world-creation.md       # Промт сотворения мира
│   └── greeting.md             # Промт приветствия игрока
├── architecture/
│   └── README.md               # Тех. архитектура: C4, стек (FastAPI, Neo4j, ChromaDB, SQLite FTS5)
├── game-loop/
│   └── README.md               # Игровой цикл: порядок хода, dice_request, 2 прохода LLM, world_pulse
├── api-spec/
│   └── README.md               # REST + WebSocket: эндпоинты, форматы JSON
├── frontend/
│   └── README.md               # Фронтенд: SPA, чат, панель Анимы, голосование
├── tech-specs/
│   ├── README.md               # Обзор версий и scope
│   ├── v0.1-mvp.md             # ТЗ v0.1 — одиночная игра
│   └── v0.2-multiplayer.md     # ТЗ v0.2 — мультиплеер
├── decisions/
│   └── README.md               # ADR: ключевые решения с обоснованиями
├── status/
│   └── README.md               # Статус: что сделано, что в работе
└── source-map/
    └── README.md               # Карта исходных чатов: chat_id → тема, ссылки
```

Содержимое каждого README.md (КРОМЕ корневого):
```markdown
# [Название темы]

> **Статус**: ⏳ TBD — будет наполнено из чатов DeepSeek (`/opt/lind/chat_deepseek/`)

## О чём этот раздел
[2-3 предложения о том, что будет содержать этот файл]

## Связанные разделы
- [Ссылки на 2-3 смежные темы из других папок]
```

Содержимое корневого README.md (`/opt/lind/adnd-knowledge/README.md`):
```markdown
# ADND Knowledge Base — База знаний проекта ADND

> **Версия**: 0.1.0 (структура)
> **Создано**: 2026-05-15
> **Источник**: 115 чатов DeepSeek (`/opt/lind/chat_deepseek/`)

## Что это
AI-читаемая база знаний по проекту ADND — настольной ролевой игры с AI-мастером (Dungeon Master на базе LLM). Содержит всю философию, механику, архитектуру и промты проекта в самодостаточных файлах.

## Для кого
- **Cline / AI-агенты** — для быстрого входа в контекст проекта
- **Разработчики** — для понимания архитектуры и принятых решений
- **Автор проекта** — как единый источник истины

## Карта разделов

| Раздел | Содержит | Статус |
|--------|----------|--------|
| [vision](vision/) | Философия, Древо Миров, Бог-Узник | ⏳ TBD |
| [game-design](game-design/) | Механики d20, магия-химия, Книги | ⏳ TBD |
| [system-prompts](system-prompts/) | Промты Экс-Ис, Анимы, мира | ⏳ TBD |
| [architecture](architecture/) | C4, стек технологий | ⏳ TBD |
| [game-loop](game-loop/) | Игровой цикл, порядок хода | ⏳ TBD |
| [api-spec](api-spec/) | REST + WebSocket спецификация | ⏳ TBD |
| [frontend](frontend/) | SPA, чат, голосование | ⏳ TBD |
| [tech-specs](tech-specs/) | ТЗ v0.1, v0.2 | ⏳ TBD |
| [decisions](decisions/) | ADR: ключевые решения | ⏳ TBD |
| [status](status/) | Статус реализации | ⏳ TBD |
| [source-map](source-map/) | Карта исходных чатов | ⏳ TBD |

## Стратегия чтения (для AI)
1. Начни с этого README — пойми общую структуру
2. Прочитай `vision/` — пойми философию и «почему»
3. Прочитай `game-design/` — пойми механику
4. Прочитай `architecture/` — пойми технический стек
5. Остальные разделы читай по необходимости
6. `system-prompts/` — самые ценные артефакты, читай когда нужно работать с промтами

## Исходные чаты
Все исходные обсуждения: `/opt/lind/chat_deepseek/` (115 чатов, 2026-04-15 — 2026-05-15)
Карта чатов: [source-map](source-map/)
```

После создания структуры:
1. Коммит в git с сообщением: `feat: create adnd-knowledge structure (12 dirs, TBD placeholders)`
2. Push в origin main (используй `scripts/sync_and_push.sh main` из `/opt/lind/`)

Корректный путь к скрипту: `/opt/lind/scripts/sync_and_push.sh`. Если скрипт нерабочий — используй `git add`, `git commit`, `git push` напрямую.
</context>

<format>
Ожидаемый результат:
1. Директория `/opt/lind/adnd-knowledge/` создана
2. Все 12 поддиректорий созданы (vision, game-design, system-prompts, architecture, game-loop, api-spec, frontend, tech-specs, decisions, status, source-map)
3. Все README.md файлы созданы в каждой папке с заглушками согласно шаблону выше
4. Дополнительные файлы в `system-prompts/`: exis-master.md, anima-assistant.md, world-creation.md, greeting.md (с заглушками)
5. Дополнительные файлы в `tech-specs/`: v0.1-mvp.md, v0.2-multiplayer.md (с заглушками)
6. Git-коммит и push выполнены
7. Вывод команды `find /opt/lind/adnd-knowledge -type f | sort` подтверждает создание всех файлов
</format>

<constraints>
- НЕ наполнять файлы реальным контентом из чатов — только заглушки (TBD)
- НЕ менять структуру других директорий проекта
- НЕ трогать существующие файлы в `/opt/lind/chat_deepseek/`, `/opt/lind/project_memory/`, `/opt/lind/backend/`
- НЕ использовать sudo без необходимости (владелец exis, прав должно хватить)
- Использовать script `sync_and_push.sh` для push, если он работает; иначе — прямой git push
- После push проверить `git status` — не должно быть незакоммиченных изменений кроме новых файлов
</constraints>