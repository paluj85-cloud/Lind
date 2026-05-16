#!/usr/bin/env python3
"""Аудит базы знаний adnd-knowledge/ через DeepSeek API (Слой 2 — LLM-критик).

Читает все 75 файлов из adnd-knowledge/, группирует по 11 разделам,
отправляет каждый раздел в DeepSeek API с промптом аудитора, собирает
все findings в единый _audit_report.json.

Запуск: cd /opt/lind && python scripts/audit_knowledge.py
"""

import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

# ── Константы ──────────────────────────────────────────────
ROOT = Path("/opt/lind")
KNOWLEDGE_DIR = ROOT / "adnd-knowledge"
PROMPT_FILE = ROOT / "project_memory" / "prompts" / "2026-05-16_audit-knowledge-base.md"
REPORT_FILE = KNOWLEDGE_DIR / "_audit_report.json"
ENV_FILE = ROOT / ".env"

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-v4-flash"
TEMPERATURE = 0.1
MAX_TOKENS = 8192
CONCURRENCY = 2
MAX_RETRIES = 3

RETRY_DELAYS_429 = [5, 10, 20]
RETRY_DELAYS_5XX = [10, 30, 60]

# Разделы для аудита (порядок: критические → важные → средние → низкие)
SECTIONS = [
    "system-prompts",
    "tech-specs",
    "decisions",
    "game-design",
    "architecture",
    "api-spec",
    "game-loop",
    "frontend",
    "vision",
    "source-map",
    "status",
]

# Файлы, которые НЕ нужно отправлять в API (служебные)
SKIP_FILES = {"_audit.json", "_source_map.json", "_classification.json", "_audit_report.json"}


# ── Утилиты ────────────────────────────────────────────────

def load_config() -> tuple[str, str]:
    """Загружает .env и промпт, возвращает (api_key, prompt_template)."""
    load_dotenv(ENV_FILE)
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY не найден в .env")
        sys.exit(1)

    if not PROMPT_FILE.exists():
        print(f"❌ Файл промпта не найден: {PROMPT_FILE}")
        sys.exit(1)

    prompt_text = PROMPT_FILE.read_text(encoding="utf-8")
    return api_key, prompt_text


def collect_section_files(section: str) -> list[dict]:
    """Собирает все .md файлы раздела (кроме служебных).

    Возвращает список {"name": "...", "path": "...", "content": "..."}
    """
    section_dir = KNOWLEDGE_DIR / section
    if not section_dir.exists():
        print(f"  ⚠️  Директория {section} не найдена, пропускаем")
        return []

    files = []
    for md_file in sorted(section_dir.glob("*.md")):
        if md_file.name in SKIP_FILES:
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
            files.append({
                "name": md_file.name,
                "path": str(md_file.relative_to(ROOT)),
                "content": content,
            })
        except Exception as e:
            print(f"  ⚠️  Ошибка чтения {md_file}: {e}")

    return files


def build_audit_prompt(prompt_template: str, section: str, files: list[dict]) -> str:
    """Формирует промпт для аудита одного раздела."""
    # Собираем содержимое файлов
    files_text = ""
    for i, f in enumerate(files, 1):
        # Ограничиваем каждый файл 3000 символами для экономии токенов
        content = f["content"]
        if len(content) > 3000:
            content = content[:3000] + "\n\n... [TRUNCATED]"
        files_text += f"\n{'='*60}\n"
        files_text += f"FILE {i}: {f['path']}\n"
        files_text += f"{'='*60}\n"
        files_text += content + "\n"

    section_prompt = f"""{prompt_template}

══════════════════════════════════════════
СЕЙЧАС АУДИРУЙ РАЗДЕЛ: {section}/
══════════════════════════════════════════

Ниже — содержимое ВСЕХ файлов раздела {section}/. Проанализируй их и верни findings ТОЛЬКО для этого раздела.

{files_text}

ВАЖНО: Верни ТОЛЬКО массив findings для раздела {section}. Без audit_metadata, без summary_by_section — только массив объектов finding.
"""

    return section_prompt


def parse_findings(response_text: str, section: str) -> list[dict]:
    """Извлекает массив findings из ответа API."""
    # Пробуем распарсить как JSON
    try:
        data = json.loads(response_text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Может быть {"findings": [...]} или просто массив внутри
            if "findings" in data:
                return data["findings"]
            # Может быть один finding
            if "id" in data:
                return [data]
            # Ищем первый массив в значениях
            for val in data.values():
                if isinstance(val, list):
                    return val
        print(f"  ⚠️  [{section}] Неожиданная структура JSON: {type(data)}")
        return []
    except json.JSONDecodeError:
        # Пробуем извлечь JSON из markdown-обёртки
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_text)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "findings" in data:
                    return data["findings"]
            except json.JSONDecodeError:
                pass

        # Пробуем найти [...] в тексте
        arr_match = re.search(r"\[\s*\{.*?\}\s*\]", response_text, re.DOTALL)
        if arr_match:
            try:
                return json.loads(arr_match.group(0))
            except json.JSONDecodeError:
                pass

        print(f"  ⚠️  [{section}] Не удалось распарсить JSON. Ответ (200 символов):")
        print(f"  {response_text[:200]}...")
        return []


# ── API вызов ──────────────────────────────────────────────

async def call_deepseek_api(
    session: aiohttp.ClientSession,
    api_key: str,
    prompt: str,
    attempt: int = 1,
) -> str | None:
    """Отправляет запрос к DeepSeek API, возвращает текст ответа или None."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }

    try:
        async with session.post(API_URL, json=payload, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=180)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

            if attempt <= MAX_RETRIES:
                if resp.status == 429:
                    delay = RETRY_DELAYS_429[min(attempt - 1, len(RETRY_DELAYS_429) - 1)]
                    print(f"    ⚠️  429 Rate limit, retry через {delay}с (попытка {attempt}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    return await call_deepseek_api(session, api_key, prompt, attempt + 1)

                if resp.status >= 500:
                    delay = RETRY_DELAYS_5XX[min(attempt - 1, len(RETRY_DELAYS_5XX) - 1)]
                    print(f"    ⚠️  {resp.status} Server error, retry через {delay}с (попытка {attempt}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    return await call_deepseek_api(session, api_key, prompt, attempt + 1)

            body = await resp.text()
            print(f"    ❌ HTTP {resp.status}: {body[:200]}")
            return None

    except asyncio.TimeoutError:
        if attempt <= MAX_RETRIES:
            print(f"    ⚠️  Timeout, retry (попытка {attempt}/{MAX_RETRIES})")
            await asyncio.sleep(10)
            return await call_deepseek_api(session, api_key, prompt, attempt + 1)
        print(f"    ❌ Timeout после {MAX_RETRIES} попыток")
        return None

    except aiohttp.ClientError as e:
        print(f"    ❌ Connection error: {e}")
        return None


# ── Основная логика ────────────────────────────────────────

async def audit_section(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    api_key: str,
    prompt_template: str,
    section: str,
) -> dict:
    """Аудирует один раздел."""
    result = {
        "section": section,
        "files_count": 0,
        "findings": [],
        "status": "pending",
        "elapsed": 0,
    }

    async with sem:
        start = time.monotonic()

        # Собираем файлы
        files = collect_section_files(section)
        result["files_count"] = len(files)

        if not files:
            print(f"📭 [{section}] Нет файлов для аудита (пропускаем)")
            result["status"] = "no_files"
            return result

        print(f"🔍 [{section}] Аудит {len(files)} файлов...")

        # Формируем промпт
        prompt = build_audit_prompt(prompt_template, section, files)
        prompt_len = len(prompt)
        print(f"    📤 Отправка промпта ({prompt_len} символов)...")

        # Отправляем в API
        response_text = await call_deepseek_api(session, api_key, prompt)

        result["elapsed"] = round(time.monotonic() - start, 1)

        if response_text is None:
            print(f"  ❌ [{section}] API вернул ошибку")
            result["status"] = "api_error"
            return result

        # Парсим findings
        findings = parse_findings(response_text, section)
        result["findings"] = findings
        result["status"] = "ok"
        result["response_len"] = len(response_text)

        print(f"  ✅ [{section}] {len(findings)} findings "
              f"({result['response_len']} символов, {result['elapsed']}с)")

        return result


async def audit_all(api_key: str, prompt_template: str) -> list[dict]:
    """Запускает параллельный аудит всех разделов."""
    return await audit_all_with_sections(api_key, prompt_template, SECTIONS)


async def audit_all_with_sections(api_key: str, prompt_template: str, sections: list[str]) -> list[dict]:
    """Запускает параллельный аудит указанных разделов."""
    sem = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            audit_section(session, sem, api_key, prompt_template, section)
            for section in sections
        ]
        results = await asyncio.gather(*tasks)

    return results


# ── Точка входа ────────────────────────────────────────────

def main():
    """Основная функция."""
    start_time = time.monotonic()

    print("📋 Загрузка конфигурации...")
    api_key, prompt_template = load_config()

    # Проверяем разделы
    print(f"\n📂 Разделы для аудита: {len(SECTIONS)}")
    for section in SECTIONS:
        section_dir = KNOWLEDGE_DIR / section
        if section_dir.exists():
            non_skip = [f for f in section_dir.glob("*.md")
                       if f.name not in SKIP_FILES]
            print(f"  {section}/: {len(non_skip)} файлов")
        else:
            print(f"  {section}/: ❌ не найден")

    # Аргументы командной строки
    dry_run_sections = None
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        dry_run_sections = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        print(f"\n🧪 Dry-run режим: только {dry_run_sections} разделов")

    sections_to_audit = SECTIONS[:dry_run_sections] if dry_run_sections else SECTIONS

    print(f"\n{'='*60}")
    print(f"🔄 Запуск аудита {len(sections_to_audit)} разделов...")
    print(f"{'='*60}\n")

    results = asyncio.run(audit_all_with_sections(api_key, prompt_template, sections_to_audit))

    print(f"\n{'='*60}")

    # Собираем все findings
    all_findings = []
    for result in results:
        all_findings.extend(result["findings"])

    # Считаем по severity
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        sev = f.get("severity", "low")
        if sev in severity_counts:
            severity_counts[sev] += 1

    # Строим отчёт
    report = {
        "audit_metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_sections_audited": len([r for r in results if r["status"] == "ok"]),
            "total_files_checked": sum(r["files_count"] for r in results),
            "findings_count": len(all_findings),
        },
        "severity_summary": severity_counts,
        "findings": all_findings,
        "section_results": [
            {
                "section": r["section"],
                "status": r["status"],
                "files_count": r["files_count"],
                "findings_count": len(r.get("findings", [])),
                "elapsed": r.get("elapsed", 0),
            }
            for r in results
        ],
    }

    # Сохраняем отчёт
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📄 Отчёт сохранён: {REPORT_FILE.relative_to(ROOT)}")

    # Статистика
    elapsed = time.monotonic() - start_time
    ok = [r for r in results if r["status"] == "ok"]
    err = [r for r in results if r["status"] not in ("ok", "no_files")]

    print(f"\n📊 Итого:")
    print(f"  Разделов: {len(ok)} OK, {len(err)} ошибок, "
          f"{len([r for r in results if r['status'] == 'no_files'])} пустых")
    print(f"  Файлов проверено: {sum(r['files_count'] for r in results)}")
    print(f"  Findings: {len(all_findings)} "
          f"(critical: {severity_counts['critical']}, "
          f"high: {severity_counts['high']}, "
          f"medium: {severity_counts['medium']}, "
          f"low: {severity_counts['low']})")
    print(f"  Время: {elapsed:.1f}с")

    if err:
        print("\n❌ Ошибки:")
        for e in err:
            print(f"  [{e['section']}] — {e['status']}")


if __name__ == "__main__":
    main()