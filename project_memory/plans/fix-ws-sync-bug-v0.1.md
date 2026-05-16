# План: Исправление бага синхронизации WebSocket

## Задача
Баг: при последовательной отправке player_action после master_speech клиент получает таймаут — бэкенд не принимает следующее сообщение.

## Решение (3 точечных фикса)

### Fix 1: Nginx — `proxy_buffering off` в `/ws` location
- **Файл**: `nginx/lind.adndexis.ru.conf`
- **Что**: добавить `proxy_buffering off;` в location /ws
- **Зачем**: Nginx по умолчанию буферизует прокси-соединения, задерживая доставку WebSocket-фреймов
- **Риск**: нулевой (стандартная практика для WebSocket)

### Fix 2: Убрать двойную отправку DiceRollRequest
- **Файл**: `backend/app/game/loop.py` (строки 222-237)
- **Что**: удалить отдельную отправку `DiceRollRequest` (строки 227-234), оставить только `MasterSpeech.dice_request`
- **Зачем**: двойное сообщение сбивает state machine клиента
- **Риск**: клиент должен уметь читать dice_request из MasterSpeech (frontend fix если нет)

### Fix 3: Fallback для пустого narrator
- **Файл**: `backend/app/game/loop.py`
- **Что**: после `_call_llm` добавить проверку — если `parsed.narrator` пуст, подставить fallback-сообщение
- **Зачем**: при ошибке LLM клиент получал пустой нарратив и зависал

## Верификация
1. `nginx -t` пройден
2. `sudo systemctl reload nginx`
3. `py_compile loop.py` пройден
4. `sudo systemctl restart lind-backend`
5. Smoke-test: greeting + player_action последовательно — без таймаута