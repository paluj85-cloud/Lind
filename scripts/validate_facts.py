#!/usr/bin/env python3
"""
Финальная валидация 10% фактов через DeepSeek API.
Проверяет: fact + source_quote соответствуют содержимому чата.

Usage: python3 scripts/validate_facts.py
"""

import json
import os
import random
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path("/opt/lind")
CHATS_DIR = PROJECT_ROOT / "chat_deepseek"
KNOWLEDGE_DIR = PROJECT_ROOT / "adnd-knowledge"
API_URL = "https://api.deepseek.com/chat/completions"
API_KEY_FILE = PROJECT_ROOT / ".cline" / "config.json"

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

SAMPLE_RATE = 0.10  # 10%
MIN_SAMPLE = 3
MAX_WORKERS = 10


def load_api_key() -> str:
    cfg = json.loads(API_KEY_FILE.read_text())
    return cfg["apiKey"]


def load_facts(section: str) -> list[dict]:
    audit_file = KNOWLEDGE_DIR / section / "_audit.json"
    if not audit_file.exists():
        return []
    return json.loads(audit_file.read_text()).get("facts", [])


def load_chat_content(chat_id: str) -> str:
    filepath = CHATS_DIR / chat_id
    if not filepath.exists():
        return ""
    return filepath.read_text()


def build_validation_prompt(fact: dict, chat_content: str) -> str:
    """Build prompt to verify a single fact."""
    system_prompt = """Ты — верификатор фактов. Проверь, соответствует ли утверждение (fact) содержимому чата.

Ответ должен быть СТРОГО в формате JSON:
{
  "verified": true/false,
  "reason": "краткое объяснение (1 предложение)",
  "match_type": "exact" | "paraphrase" | "implied" | "contradiction" | "not_found"
}

Критерии:
- "exact": source_quote дословно присутствует в чате
- "paraphrase": fact верен, но source_quote перефразирован
- "implied": fact логически следует из чата, но не утверждается прямо
- "contradiction": fact противоречит содержимому чата
- "not_found": факт не имеет отношения к содержимому чата

verified = true для exact, paraphrase, implied.
verified = false для contradiction, not_found."""

    user_prompt = f"""Факт для проверки:
- fact: {fact['fact']}
- source_quote: {fact.get('source_quote', '')}

Содержимое чата (релевантный фрагмент):
{chat_content[:8000]}

Проверь, соответствует ли факт содержимому чата."""

    return json.dumps({
        "model": "deepseek-chat",
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 500,
    })


def verify_fact(payload: str, api_key: str) -> dict:
    """Call API to verify one fact."""
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
        result = json.loads(body)
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        return {"verified": False, "reason": f"API error: {e}", "match_type": "error"}


def validate_section(section: str, api_key: str) -> dict:
    """Validate 10% of facts in a section."""
    facts = load_facts(section)
    total = len(facts)
    if total == 0:
        return {
            "section": section,
            "total_facts": 0,
            "checked": 0,
            "verified": 0,
            "accuracy": 100.0,
            "details": [],
        }

    sample_size = max(MIN_SAMPLE, int(total * SAMPLE_RATE))
    sample_size = min(sample_size, total)
    sample = random.sample(facts, sample_size)

    print(f"\n  {section}: checking {sample_size}/{total} facts...")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for fact in sample:
            chat_content = load_chat_content(fact.get("chat_id", ""))
            payload = build_validation_prompt(fact, chat_content)
            future = executor.submit(verify_fact, payload, api_key)
            futures[future] = fact

        for future in as_completed(futures):
            fact = futures[future]
            try:
                verification = future.result()
                results.append({
                    "fact_id": fact.get("fact_id", ""),
                    "fact": fact["fact"][:120],
                    "verified": verification.get("verified", False),
                    "match_type": verification.get("match_type", "unknown"),
                    "reason": verification.get("reason", ""),
                })
                status = "✓" if verification.get("verified") else "✗"
                print(f"    {status} {fact.get('fact_id', '?')}: {verification.get('match_type', '?')}")
            except Exception as e:
                results.append({
                    "fact_id": fact.get("fact_id", ""),
                    "fact": fact["fact"][:120],
                    "verified": False,
                    "match_type": "error",
                    "reason": str(e),
                })

    verified = sum(1 for r in results if r["verified"])
    accuracy = verified * 100 / len(results) if results else 100.0

    return {
        "section": section,
        "total_facts": total,
        "checked": len(results),
        "verified": verified,
        "accuracy": round(accuracy, 1),
        "details": results,
    }


def save_report(all_results: list[dict]) -> None:
    """Save validation report."""
    report_dir = PROJECT_ROOT / "project_memory" / "previous"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "stage2_validation_report.json"

    total_checked = sum(r["checked"] for r in all_results)
    total_verified = sum(r["verified"] for r in all_results)
    overall = total_verified * 100 / total_checked if total_checked > 0 else 0

    report = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall_accuracy": round(overall, 1),
        "total_checked": total_checked,
        "total_verified": total_verified,
        "threshold": 95.0,
        "passed": overall >= 95.0,
        "sections": all_results,
    }

    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nReport saved: {report_file}")
    return report


def main() -> None:
    api_key = load_api_key()
    random.seed(42)  # reproducible

    print("=" * 60)
    print("FINAL VALIDATION: 10% of facts via DeepSeek API")
    print("=" * 60)

    all_results = []
    for section in SECTIONS:
        result = validate_section(section, api_key)
        all_results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    for r in all_results:
        status = "✓ PASS" if r["accuracy"] >= 95 else "✗ FAIL"
        print(f"  {r['section']:20s}: {r['verified']}/{r['checked']} ({r['accuracy']}%) {status}")

    report = save_report(all_results)

    if report["passed"]:
        print(f"\n✓ OVERALL: {report['overall_accuracy']}% ≥ 95% — VALIDATION PASSED")
    else:
        print(f"\n✗ OVERALL: {report['overall_accuracy']}% < 95% — VALIDATION FAILED")
        print("  Review failed facts in the report before consolidation.")


if __name__ == "__main__":
    main()