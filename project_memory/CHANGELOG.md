# CHANGELOG

## [2026-05-15] — Stage 2 Complete: Knowledge Extraction & Consolidation (350 facts, 8 README.md)
- **Stage 1:** Classified 121 chats → _classification.json (107 Lind-related, 14 non-Lind)
- **Stage 2:** Extracted 350 facts from 107 Lind chats (11 batches, 10 workers parallel, DeepSeek JSON mode)
  - Sections: architecture (104), decisions (71), api-spec (44), status (38), game-design (36), vision (24), frontend (18), game-loop (15)
- **Stage 3:** Consolidated facts into 8 README.md via 8 parallel DeepSeek API requests
- **Stage 4:** Final validation — 36/36 facts verified (100%) via API with exact/paraphrase/implied match types
- Scripts created: `scripts/extract_facts.py`, `scripts/validate_facts.py`, `scripts/consolidate_facts.py`
- Reports: `project_memory/previous/stage2_validation_report.json`
- Prompts archived: `project_memory/previous/2026-05-15_stage2_extraction_prompt.md`

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

## [2026-05-14] — Project Initialization
- Cleaned up previous EternalAMS artifacts
- Reset .clinerules to template (v2.0)
- Created project_memory/ structure
- Created ORIGIN.md with TBD placeholders
- Created backend/ skeleton (app/main.py stub, tests/)
- Created scripts/sync_and_push.sh placeholder