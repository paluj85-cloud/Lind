# CHANGELOG

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