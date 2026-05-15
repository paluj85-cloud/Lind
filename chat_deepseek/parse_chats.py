#!/usr/bin/env python3
"""
Parse DeepSeek conversations.json and generate Markdown files per chat.
Handles branching: main branch first, then alternative branches.
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

INPUT_FILE = "/opt/lind/download/conversations.json"
OUTPUT_DIR = "/opt/lind/chat_deepseek"
DAYS_BACK = 30

def sanitize_filename(title: str, max_len: int = 60) -> str:
    """Convert title to safe filename."""
    # Translit common Russian chars (simple approach)
    title = title.replace(" ", "-").replace("/", "-").replace("\\", "-")
    title = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\-]', '', title)
    if len(title) > max_len:
        title = title[:max_len]
    return title.lower()

def build_branches(mapping: dict) -> list:
    """
    Build all conversation paths from the mapping.
    Returns list of (branch_label, nodes_list) where nodes_list is ordered.
    Main branch is first.
    """
    branches = []
    
    root = mapping.get("root")
    if not root or not root.get("children"):
        return branches
    
    # BFS/DFS to find all paths from root to leaves
    def dfs(node_id, path, visited):
        visited.add(node_id)
        node = mapping.get(node_id)
        if not node:
            return
        
        new_path = path + [node_id]
        children = node.get("children", [])
        
        if not children:
            # Leaf node - this is a complete branch
            branches.append(list(new_path))
        elif len(children) == 1:
            dfs(children[0], new_path, visited)
        else:
            # Branching point - follow each child
            for child in children:
                dfs(child, new_path, set(visited))
    
    root_children = root["children"]
    if len(root_children) == 1:
        dfs(root_children[0], [], set())
    else:
        for child in root_children:
            dfs(child, [], set())
    
    return branches

def build_branches_v2(mapping: dict) -> list:
    """
    Alternative: build main linear chain first, then identify side branches.
    Returns list of (branch_type, branch_nodes, branch_point_id).
    branch_type: 'main' or 'branch_from_<node_id>'
    """
    if "root" not in mapping:
        return []
    
    root = mapping["root"]
    if not root.get("children"):
        return []
    
    # Build main chain: follow the LAST child at each branching point
    # (the user's latest path)
    main_chain = []
    node_id = root["children"][0]
    
    while node_id and node_id in mapping:
        main_chain.append(node_id)
        node = mapping[node_id]
        children = node.get("children", [])
        if not children:
            break
        if len(children) == 1:
            node_id = children[0]
        else:
            # Take first child as main path (the original continuation)
            node_id = children[0]
    
    result = [("main", main_chain, None)]
    
    # Find branching points and collect alternative paths
    for i, nid in enumerate(main_chain):
        node = mapping.get(nid)
        if node and len(node.get("children", [])) > 1:
            # Alternative branches start from children[1:]
            for j, child_id in enumerate(node["children"][1:], 1):
                alt_branch = []
                cid = child_id
                while cid and cid in mapping:
                    alt_branch.append(cid)
                    ch = mapping[cid].get("children", [])
                    if not ch:
                        break
                    cid = ch[0]
                result.append((f"branch_from_{nid}_alt{j}", alt_branch, nid))
    
    return result

def format_fragment(frag: dict) -> str:
    """Format a single fragment to Markdown."""
    ftype = frag.get("type", "UNKNOWN")
    content = frag.get("content", "")
    
    if ftype == "REQUEST":
        return f"### REQUEST (пользователь)\n\n{content}\n"
    elif ftype == "RESPONSE":
        return f"### RESPONSE (ИИ)\n\n{content}\n"
    elif ftype == "THINK":
        # Collapse long thinks?
        header = "### THINK (размышления ИИ)"
        return f"{header}\n\n```\n{content}\n```\n"
    elif ftype.startswith("TOOL_"):
        tool_name = ftype.replace("TOOL_", "")
        return f"### TOOL_{tool_name}\n\n```\n{content}\n```\n"
    else:
        return f"### {ftype}\n\n{content}\n"

def generate_chat_md(chat: dict, output_dir: str) -> str:
    """Generate a Markdown file for a single chat. Returns relative path."""
    chat_id = chat["id"]
    title = chat.get("title", "Без названия")
    inserted = chat.get("inserted_at", "")
    updated = chat.get("updated_at", "")
    mapping = chat.get("mapping", {})
    
    # Collect model info from messages
    models = set()
    for nid, node in mapping.items():
        msg = node.get("message")
        if msg and msg.get("model"):
            models.add(msg["model"])
    model_str = ", ".join(sorted(models)) if models else "unknown"
    
    safe_title = sanitize_filename(title)
    if safe_title.endswith("-"):
        safe_title = safe_title[:-1]
    filename = f"{chat_id[:8]}-{safe_title}.md"
    
    # Create date subfolder
    try:
        dt = datetime.fromisoformat(updated or inserted)
        date_folder = dt.strftime("%Y-%m-%d")
    except:
        date_folder = "unknown-date"
    
    folder_path = os.path.join(output_dir, date_folder)
    os.makedirs(folder_path, exist_ok=True)
    
    filepath = os.path.join(folder_path, filename)
    
    # Build branches
    branches = build_branches_v2(mapping)
    
    node_count = len(mapping)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"- **ID**: `{chat_id}`\n")
        f.write(f"- **Дата**: {updated or inserted}\n")
        f.write(f"- **Модель**: {model_str}\n")
        f.write(f"- **Узлов**: {node_count}\n")
        f.write(f"- **Ветвлений**: {len(branches) - 1}\n\n")
        f.write("---\n\n")
        
        for branch_type, branch_nodes, branch_point in branches:
            if branch_type == "main":
                f.write("## Основная ветка\n\n")
            else:
                bp_node = mapping.get(branch_point, {})
                bp_msg = bp_node.get("message")
                bp_preview = ""
                if bp_msg:
                    frags = bp_msg.get("fragments", [])
                    for fr in frags:
                        if fr.get("type") in ("REQUEST", "RESPONSE") and fr.get("content"):
                            bp_preview = fr["content"][:80]
                            break
                f.write(f"## Ветвление: {branch_type}\n\n")
                f.write(f"*Ответвление от узла `{branch_point}` (основной ответ: «{bp_preview}...»)*\n\n")
            
            for i, nid in enumerate(branch_nodes):
                node = mapping.get(nid)
                if not node:
                    continue
                msg = node.get("message")
                if not msg:
                    continue
                
                f.write(f"### Шаг {i+1} (узел `{nid}`)\n\n")
                
                frags = msg.get("fragments", [])
                for frag in frags:
                    f.write(format_fragment(frag))
                
                f.write("---\n\n")
    
    return os.path.relpath(filepath, output_dir)


# ========== MAIN ==========
def main():
    print(f"Reading {INPUT_FILE}...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=DAYS_BACK)
    print(f"Cutoff date: {cutoff.strftime('%Y-%m-%d')} (last {DAYS_BACK} days)")
    
    recent = []
    for c in data:
        dt_str = c.get("updated_at") or c.get("inserted_at", "")
        try:
            dt = datetime.fromisoformat(dt_str)
        except:
            continue
        if dt >= cutoff:
            recent.append(c)
    
    recent.sort(key=lambda x: x.get("updated_at") or x.get("inserted_at", ""), reverse=True)
    
    print(f"Found {len(recent)} chats in date range.\n")
    
    # --- FULL MODE: process all ---
    test_mode = False
    test_count = 3
    
    if test_mode:
        print(f"=== TEST MODE: processing first {test_count} chats ===\n")
        recent = recent[:test_count]
    else:
        print(f"=== FULL MODE: processing all {len(recent)} chats ===\n")
    
    generated = []
    for i, chat in enumerate(recent):
        title = chat.get("title", "?")
        print(f"[{i+1}/{len(recent)}] {chat['id'][:8]} — {title[:70]}")
        rel_path = generate_chat_md(chat, OUTPUT_DIR)
        generated.append(rel_path)
        print(f"  -> {rel_path}")
    
    print(f"\nDone. Generated {len(generated)} files in {OUTPUT_DIR}/")
    
    # Also create test index
    index_path = os.path.join(OUTPUT_DIR, "_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Оглавление чатов (тест)\n\n")
        f.write(f"Диапазон: последние {DAYS_BACK} дней\n\n")
        f.write("| Дата | ID | Название | Файл |\n")
        f.write("|------|----|----------|------|\n")
        for chat, rel_path in zip(recent, generated):
            dt = (chat.get("updated_at") or chat.get("inserted_at", ""))[:10]
            cid = chat["id"][:8]
            title = chat.get("title", "?")
            f.write(f"| {dt} | {cid} | {title[:50]} | [{rel_path}]({rel_path}) |\n")
    
    print(f"Index: {index_path}")


if __name__ == "__main__":
    main()