# CHANGELOG

## [2026-05-16] — Аудит базы знаний: 29 находок, заполнение 5 системных промптов v5.0
- **Скрипт**: `scripts/audit_knowledge.py` — автоаудит 11 разделов, поиск противоречий и TBD-заглушек
- **Результат**: 29 находок (6 critical, 8 high, 11 medium, 4 low)
- **Этап 2 (ручная верификация)**: system-prompts/ — 5 TBD-заглушек, найдена жемчужина v5.0 (501aab82, 168 строк, «Собор Узника»)
- **Этап 3 (журнал)**: `adnd-knowledge/_audit_journal.md` — 29 находок, план консолидации, принятые решения
- **Этап 4 (консолидация)**: заполнены 5 системных промптов:
  - `exis-master.md` — 6 блоков v5.0 «Собор Узника» (из 501aab82)
  - `anima-assistant.md` — промпт Анимы (искра души)
  - `greeting.md` — ритуал первого контакта
  - `world-creation.md` — процедура сотворения мира (три Книги)
  - `README.md` — оглавление всех промптов
- **Отчёты**: `adnd-knowledge/_audit_report.json`, `adnd-knowledge/_audit_journal.md`
- Git: commit pending

## [2026-05-16] — Извлечение знаний из 62 чатов DeepSeek в adnd-knowledge/ (автоматическое, фон)
- **Скрипт**: `scripts/extract_knowledge.py` — классификация 115 чатов (core/trash/tools), массовое извлечение через DeepSeek API
- **Результат**: 62 чата обработано, 0 ошибок, 2 пропущено, время 291.4с (~5 мин)
- **База знаний**: 75 файлов в 11 разделах (api-spec:10, architecture:10, decisions:7, frontend:3, game-design:12, game-loop:3, system-prompts:13, tech-specs:15, vision:2)
- **Промт архивирован**: `project_memory/previous/extract-knowledge-script.md`
- **Файлы**: `adnd-knowledge/_classification.json`, `scripts/extract_knowledge.py`
- Git: commit pending

## [2026-05-16] — Cline Restart Protocol (Вариант B) — безопасная перезагрузка с чекпоинтом
- **Обновлён** `.clinerules` — добавлена секция «🔄 Cline Restart Protocol» (5 шагов: Save → Checkpoint → Log → Announce → Restart)
- **Обновлён** `project_memory/STATE.md` — актуальный чекпоинт перед перезагрузкой
- **Обновлён** `project_memory/progress.log` — запись о завершении
- **Prompts archived**: `2026-05-16_restart-protocol.md` → `previous/`
- **Plan archived**: `2026-05-16_restart-protocol.md` → `previous/2026-05-16_restart-protocol-plan.md`

## [2026-05-16] — Система параллельных треков (Вариант C+) — Архитектор/Инженер/Критик
- **Созданы 4 workflow-файла**:
  - `project_memory/tracks.md` — дашборд трёх треков (активный: Архитектор)
  - `project_memory/dependency-map.md` — карта зависимостей adnd-knowledge/ ↔ backend/
  - `project_memory/workflows/switch-track.md` — протокол переключения (5 шагов)
  - `project_memory/workflows/verification.md` — 3-слойная верификация (авто/LLM-критик/ручная)
- **Обновлён** `.clinerules` — секция «Parallel Tracks System» (7 TRACK RULES)
- **Обновлён** `project_memory/STATE.md` — новый чекпоинт с активным треком
- **Обновлён** `project_memory/progress.log` — запись о Phase 4→5
- Plan: `project_memory/plans/2026-05-16_parallel-tracks-options.md`
- Prompt archived: `project_memory/previous/2026-05-16_parallel-tracks-system-c-plus.md`
- Git: commit `d48d8f0`, branch `main`

## [2026-05-16] — Настройка переменных окружения (DeepSeek + GitHub)
- Создан `/opt/lind/.env` (chmod 600) с CLINE_API_KEY, DEEPSEEK_API_KEY, GITHUB_TOKEN
- Создан `/opt/lind/.gitignore` (секреты + runtime-файлы)
- systemd `lind-ttyd.service`: `Environment=` → `EnvironmentFile=/opt/lind/.env`
- `cline_launcher.sh`: добавлен source `.env` как фоллбэк для интерактивных сессий
- systemd unit скопирован в `/etc/systemd/system/`, сервис перезапущен — все три переменные проброшены
- Промт архивирован: `project_memory/previous/env-setup-2026-05-16.md`

## [2026-05-15] — Content Extraction Pipeline (Этапы 1-4): 350 фактов, 8 разделов adnd-knowledge/
- **Этап 1 (Классификация)**: 121 чат → `_classification.json` (107 Lind-related, 14 non-Lind)
- **Этап 2 (Extraction)**: `scripts/extract_facts.py` — concurrent.futures (10 workers), DeepSeek API JSON mode → 350 фактов (11 партий)
  - Sections: architecture (104), decisions (71), api-spec (44), status (38), game-design (36), vision (24), frontend (18), game-loop (15)
- **Этап 3 (Consolidation)**: `scripts/consolidate_facts.py` → 8 README.md (через API)
- **Этап 4 (Final Validation)**: `scripts/validate_facts.py` — 36/36 (100%: exact/paraphrase/implied)
- Scripts: extract_facts.py, validate_facts.py, consolidate_facts.py
- Reports: `project_memory/previous/stage2_validation_report.json`
- Prompts archived: `project_memory/previous/2026-05-15_stage2_extraction_prompt.md`
- Git: branches `feature/knowledge-extraction` merged → `main`

## [2026-05-15] — Phase 5: Acceptance & Archive for Content Extraction Pipeline
- Closed Phase 5 formally — progress.log and CHANGELOG.md updated
- Plan archived: project_memory/previous/2026-05-15_phase5-archive-extraction.md

## [2026-05-15] — Phase 5: Archive adnd-knowledge-structure task
- Closed Phase 5 (Acceptance & Archive) for adnd-knowledge-structure task
- Moved plan to project_memory/previous/2026-05-15_adnd-knowledge-structure.md
- Task complete: 12 dirs, 18 TBD files, ready for content population

## [2026-05-15] — .clinerules v3.0: EternalAMS → Lind (ADND) Redesign
- Full redesign of .clinerules from EternalAMS to Lind (ADND) project identity
- Removed local Windows infrastructure (does not exist — VPS only)
- Updated Tech Stack: adnd-knowledge/, chat_deepseek/, tmux+ttyd
- Added Project Structure section with full directory tree
- Verbatum sections preserved: Golden Rule, LLM Knowledge Standard, Pipeline (Phase 1–5), Constraints, Hooks
- Backup saved: .clinerules.v2.bak
- Git commit: 187b88c (refactor: redesign .clinerules v3.0 — Lind (ADND))
- Prompt archived: project_memory/previous/2026-05-15_clinerules-redesign-lind-v3.md

## [2026-05-15] — ADND Knowledge Structure Created
- Created adnd-knowledge/ — AI-readable knowledge base for ADND project (12 directories, 18 files)
- Structure: vision, game-design, game-loop, api-spec, frontend, architecture, tech-specs, system-prompts, decisions, status, source-map
- All files marked TBD — ready for content population from chat_deepseek/ (115 chats, 8.1 MB)
- Git pushed to origin/main (commit b87c60d)

## [2026-05-15] — Tmux prefix fix: F12 → Ctrl+\
- Changed tmux prefix from F12 to Ctrl+\ (C-\) because F12 is intercepted by browser DevTools
- Updated /opt/lind/.tmux.conf: prefix + bind with proper quoting
- Executed systemctl reload lind-tmux — session survived, config applied
- Prompt archived: project_memory/previous/2026-05-15_tmux_prefix_ctrl_backslash.md

## [2026-05-16] — Shutdown Checkpoint: STATE.md created
- Created `project_memory/STATE.md` — restart/checkpoint file for Cline reboot
- Contains: where we stopped, what's done, what's next, key files, technical state
- Updated `project_memory/progress.log`

## [2026-05-14] — Project Initialization
- Cleaned up previous EternalAMS artifacts
- Reset .clinerules to template (v2.0)
- Created project_memory/ structure
- Created ORIGIN.md with TBD placeholders
- Created backend/ skeleton (app/main.py stub, tests/)
- Created scripts/sync_and_push.sh placeholder