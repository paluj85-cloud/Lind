# Prompt: Cline Restart Protocol

---

<role>
Архитектор базы знаний Lind (ADND) — конфигурация и правила проекта. Ты отвечаешь за `.clinerules`, `project_memory/` структуру, и процедуры, обеспечивающие непрерывность работы Cline.
</role>

<task>
Добавить в `.clinerules` секцию «🔄 Cline Restart Protocol» — формальный протокол безопасной перезагрузки Cline после изменений в правилах, с сохранением состояния (STATE.md + git push) для продолжения работы после перезагрузки.
</task>

<context>
Проект: Lind (ADND) — AI-Powered Tabletop RPG Engine
Текущий git-коммит: 068c730
Активный трек: Архитектор

Файлы, которые затрагиваются:
- `/opt/lind/.clinerules` — добавить новую секцию перед `## Git Push Safety Rules`
- `/opt/lind/project_memory/STATE.md` — обновить чекпоинт (статус задачи, активный трек, дата)
- `/opt/lind/project_memory/progress.log` — запись о добавлении Restart Protocol
- `/opt/lind/project_memory/plans/2026-05-16_restart-protocol.md` — утверждённый план (Вариант B)

Текущая структура `.clinerules` (секции по порядку):
1. Project Identity
2. Tech Stack
3. Infrastructure
4. Project Structure
5. Golden Rule
6. LLM Knowledge Standard
7. Main Process: Task Pipeline (Phase 1-5)
8. Constraints
9. Automatic Hooks (Before ANY Act-mode code change, Task Pipeline Reference, Startup Check)
10. Progress Reporting
11. Parallel Tracks System
12. Git Push Safety Rules

Новая секция вставляется между `## Parallel Tracks System` и `## Git Push Safety Rules`.

Содержание новой секции:

```
## 🔄 Cline Restart Protocol

### When to restart Cline
- After ANY change to `.clinerules` — Cline reads it at chat start, changes take effect only after restart
- After structural changes to `project_memory/` (new files, new directories)
- After changes to system configs that Cline loads at startup (systemd, Nginx, tmux)

### Procedure (5 steps — ALWAYS execute in order)
1. **Save**: `git add` all changed files → `git commit` with descriptive message → `git push origin main`
2. **Checkpoint**: Update `project_memory/STATE.md`:
   - Set «Где мы остановились» to current task + status
   - Set «Последнее обновление» to current UTC timestamp
   - Set «Активный трек» if tracks are in use
3. **Log**: Add entry to `project_memory/progress.log` with timestamp, action, and status
4. **Announce**: Tell the user: «Готов к перезагрузке Cline. После перезагрузки я прочитаю STATE.md и продолжу.»
5. **Restart**: User restarts Cline → Cline reads `ORIGIN.md` → reads `STATE.md` → continues from checkpoint

### After restart
- Cline's Startup Check (defined above) already includes reading `ORIGIN.md` and `STATE.md`
- No additional steps needed — the checkpoint in `STATE.md` provides full context
```

После вставки, финальный порядок секций .clinerules:
... (всё как было) ...
## Parallel Tracks System
## 🔄 Cline Restart Protocol    ← НОВАЯ
## Git Push Safety Rules

Текущий STATE.md уже содержит актуальную информацию, но нужно обновить:
- `Последнее обновление`: 2026-05-16 09:42 UTC
- `Где мы остановились`: Задача — Cline Restart Protocol (Phase 4→5, выполняется)
- `Текущий статус`: 🔄 Добавляю секцию Restart Protocol в .clinerules. Готов к перезагрузке.
</context>

<format>
Результат — это набор изменений в репозитории:
1. **`.clinerules`** — изменённый файл с новой секцией «🔄 Cline Restart Protocol» (вставлена между Parallel Tracks System и Git Push Safety Rules)
2. **`project_memory/STATE.md`** — обновлённый чекпоинт (новая дата, статус задачи)
3. **`project_memory/progress.log`** — новая запись
4. **Git commit + push** — один коммит с сообщением: `feat: Cline Restart Protocol (safe reboot with STATE.md checkpoint)`
</format>

<constraints>
- НЕ менять другие секции `.clinerules` — только добавить новую
- НЕ менять Pipeline (Phase 1-5)
- НЕ менять Startup Check (он уже правильный)
- Использовать `scripts/sync_and_push.sh` для git push (или эквивалент: git pull --rebase + git push)
- Перед git push — проверить, что в staged changes нет файлов с секретами (GitHub Push Protection)
- НЕ включать в коммит `.bash_history`, `.bashrc`, `.tmux/`, `.gitignore` — только целевые файлы
- Язык секции: English (как весь `.clinerules`)
- Секция должна быть между `## Parallel Tracks System` и `## Git Push Safety Rules`
- После выполнения: сообщить пользователю «Готов к перезагрузке Cline»
</constraints>