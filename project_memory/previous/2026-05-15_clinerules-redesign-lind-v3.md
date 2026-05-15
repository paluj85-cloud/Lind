# Prompt: Redesign .clinerules v3.0 — Lind (ADND)

<role>
Ты — архитектор конфигурации проекта. Твоя задача: переписать `.clinerules` — главный файл правил проекта — с EternalAMS на Lind (ADND). Полный редизайн (Вариант B). Ты сохраняешь ядро методологии (Pipeline, Golden Rule, LLM Standard) нетронутым и заменяешь всё остальное актуальными данными Lind.
</role>

<task>
1. Сделать бэкап текущего `.clinerules`: `cp /opt/lind/.clinerules /opt/lind/.clinerules.v2.bak`
2. Прочитать `/opt/lind/.clinerules` (текущий v2.0) и `/opt/lind/ORIGIN.md`
3. Написать НОВЫЙ `/opt/lind/.clinerules` (v3.0) — структуру см. в `<format>`
4. Проверить что все пути, URL, имена сервисов в новом файле актуальны
5. Выполнить `git add /opt/lind/.clinerules && git commit -m "refactor: redesign .clinerules v3.0 — Lind (ADND)"`
</task>

<context>
## Проект
- **Lind (ADND)** — AI-Powered Tabletop RPG Engine
- AI-мастер (Экс-Ис) ведёт настольную RPG через веб-интерфейс
- База знаний: `adnd-knowledge/` (12 разделов, LLM-Friendly Markdown)
- Исходные данные: `chat_deepseek/` (121 экспортированных чатов с DeepSeek)
- Единственное окружение: VPS (нет локальной Windows-машины)

## Инфраструктура
- **Сервер:** VPS Hostland, IP 185.26.120.126, пользователь exis
- **Проект:** `/opt/lind`
- **Git:** `git@github.com:paluj85-cloud/Lind.git`, ветка `main`
- **Доступ:** `https://lind.adndexis.ru/cline` — ttyd WebSocket терминал (порт 7681)
- **Сервис:** `sudo systemctl restart lind-ttyd`
- **Логи:** `sudo journalctl -u lind-ttyd -f`
- **Терминал:** tmux сокет `/opt/lind/tmux/default`, сессия `lind`

## Файловая структура Lind
```
/opt/lind/
├── adnd-knowledge/       # AI-читаемая база знаний
├── chat_deepseek/        # 121 чат с DeepSeek (8.1 MB)
├── project_memory/       # Планы, промты, CHANGELOG, хуки
│   ├── hooks/before_act.md
│   ├── how_to_work_with_LLM.md
│   ├── prompt_template.md
│   ├── plans/
│   ├── prompts/
│   └── previous/
├── backend/              # FastAPI (заглушка, v0.1 в разработке)
├── nginx/                # lind.adndexis.ru.conf
├── systemd/              # lind-ttyd.service
├── scripts/              # sync_and_push.sh
├── cline_launcher.sh     # Точка входа ttyd → tmux
├── ORIGIN.md             # Контекст проекта (читать первым)
└── .clinerules           # ← ЭТОТ ФАЙЛ
```

## Что СОХРАНИТЬ без изменений (скопировать verbatim)
- **Golden Rule** — Pipeline executes for EVERY task, no exceptions
- **LLM Knowledge Standard** — always read/update how_to_work_with_LLM.md
- **Task Pipeline** — Фазы 1→5 (Analysis, Planning, Approval, Prompt Generation, Acceptance & Archive)
- **Prompt Template** — 5 immutable tags: `<role>`, `<task>`, `<context>`, `<format>`, `<constraints>`
- **Constraints** — NEVER write code without plan+prompt, NEVER deviate tech stack, ALWAYS use .env
- **Automatic Hooks** — before_act.md checklist
- **Git Push Safety Rules** — sync_and_push.sh
- **Progress Reporting** — log phase transitions

## Что ЗАМЕНИТЬ
- Project Identity: EternalAMS → Lind (ADND), AI-Powered Tabletop RPG Engine
- Tech Stack: убрать FastAPI/SQLite/pytest (пока не используется), оставить DeepSeek API, добавить adnd-knowledge, chat_deepseek, tmux/ttyd
- Infrastructure: убрать секцию «Local (Windows)», оставить только VPS
- Deploy Procedure: `eternalams` → `lind-ttyd`, `/opt/eternalams/` → `/opt/lind/`

## Что ДОБАВИТЬ
- Project Structure (карта директорий)
- Ссылка на ORIGIN.md
- Упоминание adnd-knowledge/ и chat_deepseek/

## Файлы для чтения
- `/opt/lind/.clinerules` (текущий v2.0)
- `/opt/lind/ORIGIN.md`
- `/opt/lind/nginx/lind.adndexis.ru.conf`
- `/opt/lind/systemd/lind-ttyd.service`
- `/opt/lind/scripts/sync_and_push.sh`
- `/opt/lind/cline_launcher.sh`
- `/opt/lind/project_memory/prompt_template.md`
- `/opt/lind/project_memory/hooks/before_act.md`
- `/opt/lind/project_memory/plans/2026-05-15_clinerules-redesign-lind-v3.md`

## Deploy Procedure (актуальный)
1. `git push origin main`
2. `ssh exis` → `cd /opt/lind && git pull origin main`
3. `sudo systemctl restart lind-ttyd`
4. Verify: `curl -s -o /dev/null -w "%{http_code}" https://lind.adndexis.ru/cline` → ожидается 101 (Switching Protocols) или 401 (Basic Auth)
</context>

<format>
Один файл: `/opt/lind/.clinerules` (перезаписать полностью).

Новый файл должен следовать этой структуре:

```markdown
# ⚜ Lind (ADND) Project Rules v3.0 ⚜

## Project Identity
- Project: Lind (ADND) — AI-Powered Tabletop RPG Engine
- Role: Архитектор базы знаний и оркестратор AI-мастера (Экс-Ис)
- Language: Russian for communication, English for code

## Tech Stack (ABSOLUTE — never deviate)
- DeepSeek API: deepseek-v4-pro (Cline architect), deepseek-v4-flash (app, JSON mode)
- Knowledge base: adnd-knowledge/ (12 разделов, LLM-Friendly Markdown)
- Source data: chat_deepseek/ (121 чатов, 8.1 MB)
- Terminal: tmux + ttyd (WebSocket, порт 7681)
- Shell: bash, systemd, Nginx
- VCS: git, GitHub (paluj85-cloud/Lind)

## Infrastructure
### Server (VPS — единственное окружение)
- IP: 185.26.120.126, User: exis
- Project root: /opt/lind
- Access: https://lind.adndexis.ru/cline (ttyd WebSocket через Nginx + HTTPS)
- Service: sudo systemctl restart lind-ttyd
- Logs: sudo journalctl -u lind-ttyd -f

### Deploy Procedure
1. git push origin main
2. ssh exis → cd /opt/lind && git pull origin main
3. sudo systemctl restart lind-ttyd

## Project Structure
[вставить дерево директорий из <context>]

## Golden Rule (ABSOLUTE — no exceptions, no judgement calls)
[скопировать verbatim из текущего .clinerules]

## LLM Knowledge Standard (ABSOLUTE — золотой стандарт)
[скопировать verbatim из текущего .clinerules]

## Main Process: Task Pipeline (MANDATORY)
[скопировать verbatim из текущего .clinerules]

## Constraints
[скопировать verbatim из текущего .clinerules]

## Automatic Hooks (always executed before code changes)
[скопировать verbatim из текущего .clinerules, обновить пути если нужно]

## Progress Reporting
[скопировать verbatim из текущего .clinerules]

## Git Push Safety Rules
[скопировать verbatim из текущего .clinerules]
```

Секции, помеченные «скопировать verbatim», должны быть идентичны текущему `.clinerules` — ни одной правки.
</format>

<constraints>
- НИКОГДА не изменять секции: Golden Rule, LLM Knowledge Standard, Task Pipeline, Constraints, Automatic Hooks, Prompt Template
- НИКОГДА не оставлять упоминаний EternalAMS, `/opt/eternalams/`, `eternalams.db`, `eternalams.service`
- НИКОГДА не добавлять локальное Windows-окружение (его нет)
- ВСЕГДА использовать актуальные пути: `/opt/lind`, `lind-ttyd.service`, `lind.adndexis.ru`
- ВСЕГДА сохранять бэкап перед перезаписью: `.clinerules.v2.bak`
- Файл должен быть валидным Markdown, читаемым и человеком и AI
- Секция Project Structure должна точно отражать реальное состояние `/opt/lind/` (проверить `ls -la /opt/lind/` перед записью)
- Commit message: `refactor: redesign .clinerules v3.0 — Lind (ADND)`
</constraints>