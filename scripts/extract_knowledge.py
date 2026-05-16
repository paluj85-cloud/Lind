#!/usr/bin/env python3
"""Извлечение знаний из чатов DeepSeek в adnd-knowledge/.

Читает chat_deepseek/_classification.json, фильтрует core-чаты,
отправляет каждый чат в DeepSeek API (deepseek-v4-flash) с промптом
на извлечение структурированных знаний, сохраняет результат в
adnd-knowledge/{section}/.

Запуск: cd /opt/lind && python scripts/extract_knowledge.py
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

# ── Константы ──────────────────────────────────────────────
ROOT = Path("/opt/lind")
CLASSIFICATION_FILE = ROOT / "chat_deepseek" / "_classification.json"
CHAT_DIR = ROOT / "chat_deepseek"
KNOWLEDGE_DIR = ROOT / "adnd-knowledge"
ENV_FILE = ROOT / ".env"

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"
TEMPERATURE = 0.1
MAX_TOKENS = 4096
CONCURRENCY = 3
MAX_RETRIES = 3

# Паузы для retry (секунды)
RETRY_DELAYS_429 = [5, 10, 20]      # rate limit
RETRY_DELAYS_5XX = [10, 30, 60]     # server error

# ── Промпт-шаблон ──────────────────────────────────────────
EXTRACTION_PROMPT = """Ты — анализатор знаний. Извлеки из чата ниже структурированные знания в LLM-Friendly Markdown.

Формат ответа (строго):
# {title}
**Дата извлечения**: {date}
**Источник**: {chat_id}
**Раздел**: {section}

## Суть
{{1-3 предложения — главная мысль чата}}

## Ключевые тезисы
- {{тезис 1}}
- {{тезис 2}}
...

## Связи
- Связано с: {{ссылки на другие разделы}}

Чат:
{chat_content}"""


# ── Утилиты ────────────────────────────────────────────────

def load_config() -> tuple[str, list[dict]]:
    """Загружает .env и _classification.json, возвращает (api_key, chats)."""
    load_dotenv(ENV_FILE)
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY не найден в .env")
        sys.exit(1)

    with open(CLASSIFICATION_FILE, encoding="utf-8") as f:
        all_chats = json.load(f)

    # Фильтруем только core
    core_chats = [c for c in all_chats if c.get("status") == "core"]
    print(f"📋 Загружено {len(all_chats)} чатов, "
          f"core: {len(core_chats)}, "
          f"trash: {len([c for c in all_chats if c.get('status') == 'trash'])}, "
          f"tools: {len([c for c in all_chats if c.get('status') == 'tools'])}")

    return api_key, core_chats


def load_chat_content(chat: dict) -> str | None:
    """Читает содержимое .md файла чата по date/id."""
    date_str = chat["date"]
    chat_id = chat["id"]
    date_dir = CHAT_DIR / date_str

    if not date_dir.exists():
        print(f"⚠️  Директория не найдена: {date_dir}")
        return None

    # Ищем файл по префиксу id
    for f in date_dir.glob(f"{chat_id}*.md"):
        return f.read_text(encoding="utf-8")

    print(f"⚠️  Файл не найден: {date_dir}/{chat_id}*.md")
    return None


def build_prompt(chat: dict, content: str) -> str:
    """Формирует промпт для DeepSeek API."""
    from datetime import datetime, UTC
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    sections = ", ".join(chat.get("sections", ["unknown"]))
    return EXTRACTION_PROMPT.format(
        title=chat["title"],
        date=today,
        chat_id=chat["id"],
        section=sections,
        chat_content=content,
    )


def get_output_path(chat: dict) -> Path:
    """Определяет путь для сохранения результата.

    Использует первый раздел из sections как директорию.
    Имя файла формируется из id и нормализованного title.
    """
    sections = chat.get("sections", ["unknown"])
    primary_section = sections[0]

    # Нормализуем title в имя файла
    import re
    title_slug = chat["title"].lower()
    title_slug = re.sub(r"[^\w\s-]", "", title_slug)  # убираем спецсимволы
    title_slug = re.sub(r"\s+", "-", title_slug)       # пробелы → дефисы
    title_slug = title_slug[:50]                       # обрезаем до 50 символов

    filename = f"{chat['id']}-{title_slug}.md"
    return KNOWLEDGE_DIR / primary_section / filename


def output_exists(chat: dict) -> bool:
    """Проверяет, существует ли уже файл для этого чата."""
    path = get_output_path(chat)
    if path.exists():
        # Проверяем, что в файле есть упоминание chat_id (точно наш файл)
        content = path.read_text(encoding="utf-8")
        if chat["id"] in content:
            return True
    return False


# ── API вызов ──────────────────────────────────────────────

async def call_deepseek_api(
    session: aiohttp.ClientSession,
    api_key: str,
    system_prompt: str,
    attempt: int = 1,
) -> str | None:
    """Отправляет запрос к DeepSeek API, возвращает текст ответа или None.

    При ошибках выполняет retry с exponential backoff.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": system_prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }

    try:
        async with session.post(API_URL, json=payload, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

            # Ошибки с retry
            if attempt <= MAX_RETRIES:
                if resp.status == 429:
                    delay = RETRY_DELAYS_429[min(attempt - 1, len(RETRY_DELAYS_429) - 1)]
                    print(f"  ⚠️  429 Rate limit, retry через {delay}с (попытка {attempt}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    return await call_deepseek_api(session, api_key, system_prompt, attempt + 1)

                if resp.status >= 500:
                    delay = RETRY_DELAYS_5XX[min(attempt - 1, len(RETRY_DELAYS_5XX) - 1)]
                    print(f"  ⚠️  {resp.status} Server error, retry через {delay}с (попытка {attempt}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    return await call_deepseek_api(session, api_key, system_prompt, attempt + 1)

            # Не-retryable ошибка
            body = await resp.text()
            print(f"  ❌ HTTP {resp.status}: {body[:200]}")
            return None

    except asyncio.TimeoutError:
        if attempt <= MAX_RETRIES:
            print(f"  ⚠️  Timeout, retry (попытка {attempt}/{MAX_RETRIES})")
            await asyncio.sleep(10)
            return await call_deepseek_api(session, api_key, system_prompt, attempt + 1)
        print(f"  ❌ Timeout после {MAX_RETRIES} попыток")
        return None

    except aiohttp.ClientError as e:
        print(f"  ❌ Connection error: {e}")
        return None


# ── Основная логика ────────────────────────────────────────

async def extract_one(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    api_key: str,
    chat: dict,
) -> dict:
    """Обрабатывает один чат: читает → отправляет в API → сохраняет результат."""
    chat_id = chat["id"]
    result = {"chat_id": chat_id, "title": chat["title"], "status": "pending"}

    async with sem:
        # Проверяем, не извлечён ли уже
        if output_exists(chat):
            print(f"⏭️  [{chat_id}] Уже извлечён → {get_output_path(chat)}")
            result["status"] = "skipped"
            return result

        # Читаем чат
        content = load_chat_content(chat)
        if content is None:
            result["status"] = "no_file"
            return result

        # Формируем промпт
        prompt = build_prompt(chat, content)
        print(f"📤 [{chat_id}] Отправка ({len(content)} символов)...")

        # Отправляем в API
        response_text = await call_deepseek_api(session, api_key, prompt)

        if response_text is None:
            print(f"❌ [{chat_id}] {chat['title']} — API вернул ошибку")
            result["status"] = "api_error"
            return result

        # Сохраняем результат
        output_path = get_output_path(chat)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(response_text, encoding="utf-8")

        print(f"✅ [{chat_id}] → {output_path.relative_to(ROOT)} "
              f"({len(response_text)} символов)")
        result["status"] = "ok"
        result["output"] = str(output_path.relative_to(ROOT))
        return result


async def extract_all(api_key: str, chats: list[dict]) -> list[dict]:
    """Запускает параллельное извлечение всех чатов."""
    sem = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            extract_one(session, sem, api_key, chat)
            for chat in chats
        ]
        results = await asyncio.gather(*tasks)

    return results


# ── Точка входа ────────────────────────────────────────────

def main():
    """Основная функция."""
    start_time = time.monotonic()

    # Загрузка конфигурации
    api_key, core_chats = load_config()

    # Фильтр: только ещё не извлечённые
    pending = [c for c in core_chats if not output_exists(c)]
    skipped = len(core_chats) - len(pending)
    print(f"\n🔄 К обработке: {len(pending)} чатов "
          f"(уже извлечено: {skipped}, пропущено: 0)")

    if not pending:
        print("✨ Все чаты уже извлечены!")
        return

    # Аргументы командной строки: --dry-run N — обработать только N чатов
    dry_run = None
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        dry_run = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        pending = pending[:dry_run]
        print(f"🧪 Dry-run режим: только {len(pending)} чатов")

    # Запуск
    print(f"{'='*60}")
    results = asyncio.run(extract_all(api_key, pending))
    print(f"{'='*60}")

    # Статистика
    ok = [r for r in results if r["status"] == "ok"]
    err = [r for r in results if r["status"] not in ("ok", "skipped", "pending")]

    elapsed = time.monotonic() - start_time
    print(f"\n📊 Итого: {len(ok)} OK, {len(err)} ошибок, "
          f"{skipped} пропущено, за {elapsed:.1f}с")

    if err:
        print("\n❌ Ошибки:")
        for e in err:
            print(f"  [{e['chat_id']}] {e['title']} — {e['status']}")


if __name__ == "__main__":
    main()