#!/usr/bin/env python3
"""
Этап 3: Глобальная консолидация фактов в README.md.
Для каждого из 8 разделов собирает факты из _audit.json,
группирует по топикам и генерирует структурированный README.md через DeepSeek API.

Usage: python3 scripts/consolidate_facts.py
"""

import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path("/opt/lind")
KNOWLEDGE_DIR = PROJECT_ROOT / "adnd-knowledge"
API_URL = "https://api.deepseek.com/chat/completions"
API_KEY_FILE = PROJECT_ROOT / ".cline" / "config.json"

SECTIONS = {
    "vision": "Видение продукта",
    "game-design": "Игровая механика",
    "game-loop": "Игровой цикл",
    "api-spec": "API-спецификации",
    "frontend": "Фронтенд",
    "architecture": "Архитектура",
    "decisions": "Ключевые решения",
    "status": "Статус проекта",
}

MAX_WORKERS = 8  # 8 разделов → 8 параллельных запросов


def load_api_key() -> str:
    cfg = json.loads(API_KEY_FILE.read_text())
    return cfg["apiKey"]


def load_facts(section: str) -> list[dict]:
    audit_file = KNOWLEDGE_DIR / section / "_audit.json"
    if not audit_file.exists():
        return []
    return json.loads(audit_file.read_text()).get("facts", [])


def build_consolidation_prompt(section: str, facts: list[dict]) -> str:
    """Build prompt to consolidate facts into README.md."""
    section_name = SECTIONS.get(section, section)

    # Group facts by topic
    topics: dict[str, list[dict]] = {}
    for f in facts:
        topic = f.get("topic", "Общее").strip()
        if not topic:
            topic = "Общее"
        topics.setdefault(topic, []).append(f)

    # Build facts summary for prompt
    facts_text_parts = []
    for topic, items in sorted(topics.items()):
        facts_text_parts.append(f"\n## {topic}")
        for item in items:
            conf = item.get("confidence", "medium")
            fact_text = item["fact"]
            quote = item.get("source_quote", "")[:150]
            facts_text_parts.append(f"- [{conf}] {fact_text}")
            if quote:
                facts_text_parts.append(f"  Источник: «{quote}»")

    facts_text = "\n".join(facts_text_parts)

    system_prompt = f"""Ты — технический писатель проекта Lind (ADND) — AI-Powered Tabletop RPG Engine.
Твоя задача: на основе извлечённых фактов составить README.md для раздела «{section_name}».

Формат README.md:
1. Заголовок H1: название раздела
2. Краткое описание раздела (1-2 предложения)
3. Содержание (оглавление)
4. Сгруппированные по темам подразделы с H2/H3 заголовками
5. Для каждого факта — маркированный список с ключевыми утверждениями
6. В конце — раздел «Сводка» с 3-5 ключевыми выводами

ПРАВИЛА:
- Только факты из предоставленного списка. Никаких домыслов.
- Группируй похожие факты вместе, удаляй дубликаты.
- Сохраняй confidence: high-факты приоритетнее.
- Пиши на русском языке.
- Используй GitHub-совместимый Markdown.
- Не упоминай конкретные ID чатов или source_quote в итоговом тексте (это meta-информация).
- Факты из source_quote перефразируй своими словами, не копируй дословно длинные цитаты.

Выдай ГОТОВЫЙ README.md — просто Markdown, без обёрток и пояснений."""

    user_prompt = f"""Раздел: {section_name}
Всего фактов: {len(facts)}

Факты для консолидации:

{facts_text[:12000]}

Составь README.md."""

    return json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 8000,
    })


def call_api(payload: str, api_key: str) -> str:
    """Call DeepSeek API, return content string."""
    data = payload.encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = resp.read().decode("utf-8")
    result = json.loads(body)
    return result["choices"][0]["message"]["content"]


def consolidate_section(section: str, api_key: str) -> tuple[str, str, int]:
    """Consolidate one section. Returns (section, readme_content, facts_count)."""
    facts = load_facts(section)
    if not facts:
        return section, f"# {SECTIONS.get(section, section)}\n\nРаздел в разработке. Факты не извлечены.\n", 0

    payload = build_consolidation_prompt(section, facts)
    content = call_api(payload, api_key)

    # Save
    readme_file = KNOWLEDGE_DIR / section / "README.md"
    readme_file.parent.mkdir(parents=True, exist_ok=True)
    readme_file.write_text(content)

    return section, content, len(facts)


def main() -> None:
    api_key = load_api_key()

    print("=" * 60)
    print("CONSOLIDATION: Facts → README.md (8 sections)")
    print("=" * 60)

    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(consolidate_section, section, api_key): section
            for section in SECTIONS
        }

        for future in as_completed(futures):
            section = futures[future]
            try:
                section_name, content, count = future.result()
                results[section] = {"name": section_name, "facts": count, "chars": len(content)}
                print(f"  [OK] {section:20s}: {count:3d} facts → {len(content):5d} chars README.md")
            except Exception as e:
                print(f"  [ERR] {section}: {e}")

    # Summary
    print(f"\n{'='*60}")
    print("CONSOLIDATION COMPLETE")
    print(f"{'='*60}")
    total_facts = sum(r["facts"] for r in results.values())
    print(f"Total facts consolidated: {total_facts}")
    print(f"Sections: {len(results)}/8")

    # Update _audit.json with consolidation timestamp
    for section in results:
        audit_file = KNOWLEDGE_DIR / section / "_audit.json"
        if audit_file.exists():
            audit = json.loads(audit_file.read_text())
            audit["consolidated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            audit["readme_size_chars"] = results[section]["chars"]
            audit_file.write_text(json.dumps(audit, ensure_ascii=False, indent=2))

    print("Timestamps updated in _audit.json files.")


if __name__ == "__main__":
    main()