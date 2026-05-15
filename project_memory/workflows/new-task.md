# New Task Workflow

## Phase 1: Analysis
1. User describes the task.
2. Ask clarifying questions until you have complete clarity.
3. Turn vague requests into precise technical specifications.
4. Log: `project_memory/progress.log` — "Phase 1: Analysis started"

## Phase 2: Planning
1. Say: «Я готов перейти к планированию. Скажи ПЛАН.»
2. After user says `ПЛАН`, create a plan file in `project_memory/prompts/plan_<task-slug>.md`
3. Propose 2-3 solution options with pros/cons.
4. Show the plan and wait.
5. Log: `project_memory/progress.log` — "Phase 2: Plan created"

## Phase 3: Approval
1. Wait for user to say: `ПЛАН УТВЕРЖДАЮ`.
2. Do NOT proceed until approval is given.
3. Log: `project_memory/progress.log` — "Phase 3: Plan approved"

## Phase 4: Prompt Generation
1. Read `project_memory/prompt_template.md`
2. Fill in all 5 tags: `<role>`, `<task>`, `<context>`, `<format>`, `<constraints>`
3. Save prompt to `project_memory/prompts/prompt_<task-slug>.md`
4. Tell user: «Вставь это в новый чат Cline (Act). Прочти [prompt file]. Начинай.»
5. Log: `project_memory/progress.log` — "Phase 4: Prompt generated"

## Phase 5: Acceptance & Archive
1. After task is executed in new chat, verify result against acceptance criteria.
2. Move files from `project_memory/prompts/` to `project_memory/previous/`
3. Add entry to `project_memory/CHANGELOG.md`
4. Report: «Задача выполнена и задокументирована.»
5. Log: `project_memory/progress.log` — "Phase 5: Task archived"