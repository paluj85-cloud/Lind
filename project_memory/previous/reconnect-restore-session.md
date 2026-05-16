# Prompt: Восстановление сессии при перезагрузке (Вариант A)

<role>
Ты — full-stack инженер проекта Lind (ADND). Ты работаешь с FastAPI + WebSocket (Python) и vanilla JavaScript фронтендом. Ты изменяешь существующий код минимально инвазивно, сохраняя обратную совместимость.
</role>

<task>
Реализовать восстановление игровой сессии при перезагрузке страницы/реконнекте: фронтенд сохраняет session_id в localStorage и передаёт его при переподключении, сервер восстанавливает сессию вместо создания новой и отправляет backlog всех сообщений.
</task>

<context>

## Проблема
- Каждый новый WebSocket создаёт новую сессию (main.py:85 `uuid4()`)
- Фронтенд шлёт `player_join` → сервер запускает приветствие заново
- Игрок теряет историю при перезагрузке страницы

## Файлы для изменения

### 1. `backend/static/app.js` (233 строки)
- Строка 10: `let sessionId = null;` — текущее состояние
- Строка 109-111: `ws.onopen` — после коннекта ничего не делает, ждёт session_created
- Строка 143-151: `handleMessage` → `session_created` — получает sessionId и шлёт player_join
- Строка 157-167: `handleMessage` → `master_speech` — рендерит narrator
- **Нужно добавить**: localStorage для session_id, передача session_id в player_join, обработка backlog в master_speech

### 2. `backend/app/main.py` (152 строки)
- Строка 85: `session_id = str(uuid4())` — всегда новый UUID
- Строка 86-87: создание сессии + отправка session_created
- Строка 106-112: обработка `player_join` — всегда запускает приветствие
- **Нужно изменить**: при получении player_join с существующим session_id — восстановить сессию вместо создания новой

### 3. `backend/app/game/loop.py` (281 строка)
- Строка 41-49: GameLoop API — start_greeting, handle_player_input, handle_dice_result
- Строка 163-200: `start_greeting()` — 2-шаговое приветствие
- **Нужно добавить**: метод `restore_session(player_name)` — загружает историю из БД и отправляет backlog

### 4. `backend/app/db.py` (366 строк)
- Строка 119-242: операции с сессиями и сообщениями
- Существующая функция `get_recent_messages()` — используется для контекста LLM
- **Нужно проверить/добавить**: функция `get_session_messages()` — получение ВСЕХ сообщений сессии для backlog

## Протокол (новые сообщения)

### Client → Server (изменено)
```json
{"type": "player_join", "player_name": "...", "session_id": "uuid-или-null"}
```

### Server → Client (новое поле в master_speech)
```json
{
  "type": "master_speech",
  "narrator": "...",
  "dice_request": null,
  "backlog": [
    {"role": "master", "content": "...", "timestamp": "..."},
    {"role": "player", "content": "...", "timestamp": "..."}
  ]
}
```

## Логика

### Фронтенд (app.js)
1. При `session_created` → сохранить `sessionId` в `localStorage` ('lind_session_id')
2. При отправке `player_join` → добавить поле `session_id` со значением из localStorage (или null)
3. При получении `master_speech` с полем `backlog` → отрендерить все backlog-сообщения перед narrator
4. При `ws.onopen` (реконнект с имеющимся sessionId) → не ждать session_created, сразу слать player_join

### Сервер (main.py)
1. В `player_join`: если `msg.get("session_id")` передан и не пуст → проверить существование сессии через `get_session()`
2. Если сессия существует и status='active':
   - **Не создавать новую сессию**
   - Переиспользовать существующий `session_id`
   - Вызвать `loop.restore_session(player_name)` вместо `loop.start_greeting(player_name)`
3. Если сессии нет (истекла, удалена) или session_id не передан:
   - Работать как сейчас: создать новую сессию, запустить приветствие

### GameLoop (loop.py)
1. Метод `restore_session(player_name)`:
   - Загрузить ВСЕ сообщения сессии из БД
   - Сформировать backlog: список `{role, content, timestamp}`
   - Обновить player_name в сессии
   - Не вызывать LLM, не запускать приветствие
   - Отправить `master_speech` с `narrator`: короткое сообщение о возвращении + `backlog` со всей историей
   - Текст narrator: «Ты возвращаешься. Нити судьбы помнят тебя.» или подобное

</context>

<format>
Изменения в 4 файлах:
1. `backend/static/app.js` — модифицированные строки с localStorage и backlog
2. `backend/app/main.py` — модифицированная строка 85 и блок player_join
3. `backend/app/game/loop.py` — новый метод restore_session()
4. `backend/app/db.py` — новая функция get_session_messages() (если нужно)

Каждый файл — через SEARCH/REPLACE блоки в replace_in_file.
</format>

<constraints>
- НЕ менять сигнатуры существующих публичных методов
- НЕ ломать новую сессию (без localStorage) — должен работать как раньше
- НЕ добавлять новых зависимостей
- Сохранять обратную совместимость протокола: `master_speech` без backlog должен работать
- Использовать только Python 3.11+ и vanilla JS
- Минимизировать изменения: целевой объём < 60 строк нового кода
- Новый метод restore_session НЕ вызывает LLM — только читает БД и шлёт backlog
- При восстановлении НЕ запускать приветствие
</constraints>