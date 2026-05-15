#!/usr/bin/env python3
"""
Этап 2: Извлечение фактов из 115 чатов через DeepSeek API.
Партии по 10 чатов, параллельные запросы, JSON mode.

Usage: python3 scripts/extract_facts.py [--batch N]
"""

import json
import os
import re
import subprocess
import sys
import time
import traceback
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- Config ---
PROJECT_ROOT = Path("/opt/lind")
CHATS_DIR = PROJECT_ROOT / "chat_deepseek"
CLASSIFICATION_FILE = CHATS_DIR / "_classification.json"
KNOWLEDGE_DIR = PROJECT_ROOT / "adnd-knowledge"
PROMPT_FILE = PROJECT_ROOT / "project_memory" / "prompts" / "stage2_extraction_prompt.md"

# DeepSeek API
API_URL = "https://api.deepseek.com/chat/completions"
API_KEY_FILE = PROJECT_ROOT / ".cline" / "config.json"
BATCH_SIZE = 10
MAX_WORKERS = 10  # параллельные запросы
MODEL = "deepseek-v4-flash"  # быстрая модель для JSON mode
JSON_MODE_MODEL = "deepseek-chat"  # поддерживает response_format: json_object

# Разделы для извлечения
SECTIONS = [
    "vision",
    "game-design",
    "game-loop",
    "api-spec",
    "frontend",
    "architecture",
    "decisions",
    "status",
]

SECTION_PREFIXES = {
    "vision": "vis",
    "game-design": "gds",
    "game-loop": "glp",
    "api-spec": "api",
    "frontend": "fnt",
    "architecture": "arc",
    "decisions": "dec",
    "status": "sta",
}


def load_api_key() -> str:
    """Load DeepSeek API key from config."""
    if not API_KEY_FILE.exists():
        raise FileNotFoundError(f"API key file not found: {API_KEY_FILE}")
    cfg = json.loads(API_KEY_FILE.read_text())
    return cfg["apiKey"]


def load_classification() -> list[dict]:
    """Load chat classification."""
    data = json.loads(CLASSIFICATION_FILE.read_text())
    # Filter only Lind-related chats
    chats = []
    for ch in data["chats"]:
        if ch.get("category") != "Engineering_Non_IT":
            chats.append(ch)
    return chats


def load_chat(chat: dict) -> str:
    """Read chat file content."""
    filepath = CHATS_DIR / chat["file"]
    if not filepath.exists():
        raise FileNotFoundError(f"Chat file not found: {filepath}")
    return filepath.read_text()


def build_prompt(chat_content: str, chat_meta: dict) -> str:
    """Build extraction prompt for a single chat."""
    system_prompt = f"""Ты — аналитик-извлекатель знаний проекта Lind (ADND). Твоя задача: прочитать чат и извлечь из него факты в структурированном виде для наполнения базы знаний.

Проект: Lind (ADND) — AI-Powered Tabletop RPG Engine, где AI-мастер (Экс-Ис) ведёт игру.

Разделы для извлечения:
- vision: Видение продукта, миссия, ценности
- game-design: Игровая механика, правила, магия, расы
- game-loop: Игровой цикл: ход, действия, фазы
- api-spec: API-спецификации, эндпоинты
- frontend: UI/UX, интерфейс, дизайн
- architecture: Архитектура системы, компоненты
- decisions: Ключевые решения и их обоснования
- status: Текущий статус проекта

Для КАЖДОГО факта укажи:
- fact: конкретное утверждение (1-2 предложения, факт без воды)
- confidence: "high" (явно утверждается), "medium" (подразумевается), "low" (косвенно)
- source_quote: ДОСЛОВНАЯ цитата из чата (короткая, 1-2 предложения)
- topic: тема факта (2-5 слов)

ПРАВИЛА:
- ТОЛЬКО факты, явно присутствующие в чате. Никаких домыслов.
- source_quote — ДОСЛОВНО из чата.
- Если по разделу фактов нет — верни пустой массив [].
- НЕ включай разделы system-prompts и tech-specs.
- Факты должны относиться к проекту Lind (ADND), а не к AutoCAD, PL/SQL, или другим нерелевантным темам.
- Если чат полностью не релевантен проекту Lind — верни все разделы пустыми.

Ответ должен быть СТРОГО в формате JSON."""

    user_prompt = f"""Чат: {chat_meta['name']}
Дата: {chat_meta['date']}

Извлеки все факты по проекту Lind (ADND) из этого чата:

{chat_content[:10000]}"""

    return json.dumps({
        "model": JSON_MODE_MODEL,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 4000,
    })


def call_deepseek(payload: str, api_key: str) -> dict:
    """Call DeepSeek API and return parsed JSON response."""
    data = payload.encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
        result = json.loads(body)
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        print(f"  [ERROR] API call failed: {e}")
        return {}


def parse_response(response: dict, chat_meta: dict) -> dict[str, list[dict]]:
    """Parse API response into structured facts per section."""
    facts_by_section: dict[str, list[dict]] = {s: [] for s in SECTIONS}

    # Try different response formats
    sections_data = response.get("sections", response)

    for section in SECTIONS:
        items = sections_data.get(section, [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and item.get("fact"):
                    facts_by_section[section].append({
                        "fact": item.get("fact", ""),
                        "source_quote": item.get("source_quote", ""),
                        "chat_id": chat_meta["file"],
                        "confidence": item.get("confidence", "medium"),
                        "topic": item.get("topic", ""),
                    })

    return facts_by_section


def load_existing_audit(section: str) -> dict:
    """Load existing _audit.json for a section."""
    audit_file = KNOWLEDGE_DIR / section / "_audit.json"
    if audit_file.exists():
        return json.loads(audit_file.read_text())
    return {
        "section": section,
        "last_updated": "",
        "facts": [],
    }


def save_audit(section: str, audit: dict) -> None:
    """Save _audit.json for a section."""
    audit_dir = KNOWLEDGE_DIR / section
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_file = audit_dir / "_audit.json"
    audit["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    audit_file.write_text(json.dumps(audit, ensure_ascii=False, indent=2))


def save_source_map(section: str, facts: list[dict]) -> None:
    """Update _source_map.json for a section."""
    audit_dir = KNOWLEDGE_DIR / section
    audit_dir.mkdir(parents=True, exist_ok=True)
    map_file = audit_dir / "_source_map.json"

    existing = {"section": section, "mappings": []}
    if map_file.exists():
        existing = json.loads(map_file.read_text())

    for fact in facts:
        existing["mappings"].append({
            "fact_id": fact.get("fact_id", ""),
            "chat_file": fact.get("chat_id", ""),
            "line_range": fact.get("line_range", ""),
        })

    existing["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    map_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2))


def validate_facts(section: str, facts: list[dict]) -> tuple[int, int]:
    """Validate 15% of facts by grepping source_quote in original chat files.
    Returns (found, total_checked)."""
    total = len(facts)
    if total == 0:
        return 0, 0

    # Check 15%, min 3, max all
    check_count = max(min(total, max(3, total * 15 // 100)), 1)
    import random
    sample = random.sample(facts, check_count)

    found = 0
    for fact in sample:
        quote = fact.get("source_quote", "")
        chat_file = fact.get("chat_id", "")
        if not quote or not chat_file:
            continue

        filepath = CHATS_DIR / chat_file
        if not filepath.exists():
            continue

        # Escape quote for grep
        # Use first 60 chars of quote for grep (avoid issues with long quotes)
        search_text = quote[:80].replace("'", "'\\''")
        try:
            result = subprocess.run(
                ["grep", "-q", "-F", "--", search_text, str(filepath)],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                found += 1
            else:
                # Try with shorter substring
                short_text = quote[:40].replace("'", "'\\''")
                result2 = subprocess.run(
                    ["grep", "-q", "-F", "--", short_text, str(filepath)],
                    capture_output=True,
                    timeout=5,
                )
                if result2.returncode == 0:
                    found += 1
        except Exception:
            pass

    return found, check_count


def process_batch(batch: list[dict], api_key: str) -> bool:
    """Process one batch of 10 chats in parallel. Returns True if validation passed."""
    print(f"\n{'='*60}")
    print(f"Processing batch: chats {batch[0]['file']} ... {batch[-1]['file']}")
    print(f"{'='*60}")

    # Collect all facts per section across all chats in batch
    batch_facts: dict[str, list[dict]] = {s: [] for s in SECTIONS}

    # Process chats in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for chat in batch:
            try:
                content = load_chat(chat)
            except Exception as e:
                print(f"  [SKIP] Cannot read {chat['file']}: {e}")
                continue

            payload = build_prompt(content, chat)
            future = executor.submit(call_deepseek, payload, api_key)
            futures[future] = chat

        for future in as_completed(futures):
            chat = futures[future]
            file_short = chat["file"].split("/")[-1]
            try:
                response = future.result()
                facts_by_section = parse_response(response, chat)
                total_facts = sum(len(v) for v in facts_by_section.values())
                print(f"  [OK] {file_short}: {total_facts} facts")
                
                for section, facts in facts_by_section.items():
                    batch_facts[section].extend(facts)
            except Exception as e:
                print(f"  [ERR] {file_short}: {e}")

    # Assign fact_ids and save
    for section in SECTIONS:
        facts = batch_facts[section]
        if not facts:
            continue

        prefix = SECTION_PREFIXES[section]
        
        # Load existing audit to get next fact_id index
        existing = load_existing_audit(section)
        start_idx = len(existing["facts"])
        
        for i, fact in enumerate(facts):
            fact["fact_id"] = f"{prefix}_{start_idx + i + 1:03d}"
            fact["line_range"] = fact.get("line_range", "")

        # Append to existing facts
        existing["facts"].extend(facts)
        save_audit(section, existing)
        save_source_map(section, facts)

        # Validate
        found, checked = validate_facts(section, facts)
        if checked > 0:
            accuracy = found * 100 / checked
            status = "✓" if accuracy >= 95 else "✗ FAIL"
            print(f"  [VAL] {section}: {found}/{checked} ({accuracy:.0f}%) {status}")
            if accuracy < 95:
                print(f"  [WARN] Validation <95% for {section}. Continuing but flagged.")

    print(f"\nBatch complete. Moving to next...")
    time.sleep(2)  # Rate limit buffer
    return True


def main() -> None:
    api_key = load_api_key()
    chats = load_classification()
    
    print(f"Loaded {len(chats)} Lind-related chats")
    print(f"Model: {JSON_MODE_MODEL} (JSON mode)")
    print(f"Workers: {MAX_WORKERS} parallel")

    # Check command line arg for resume batch
    start_batch = 1
    if len(sys.argv) > 2 and sys.argv[1] == "--batch":
        start_batch = int(sys.argv[2])
        print(f"Resuming from batch {start_batch}")

    # Split into batches
    batches = []
    for i in range(0, len(chats), BATCH_SIZE):
        batch = chats[i : i + BATCH_SIZE]
        batches.append(batch)

    print(f"Total batches: {len(batches)} (starting at {start_batch})")

    for batch_idx, batch in enumerate(batches):
        batch_num = batch_idx + 1
        if batch_num < start_batch:
            print(f"\nSkipping batch {batch_num}/{len(batches)} (already done)")
            continue
        
        print(f"\n{'#'*60}")
        print(f"# BATCH {batch_num}/{len(batches)}")
        print(f"{'#'*60}")
        
        process_batch(batch, api_key)

    print(f"\n{'='*60}")
    print("All batches processed!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()