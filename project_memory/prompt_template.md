# Prompt Template

Use this structure for EVERY generated prompt.

---

<role>
[Define the role: who is the AI in this task? E.g., "Senior Python backend developer", "DevOps engineer", "QA tester"]
</role>

<task>
[Precise, one-sentence description of WHAT to do. E.g., "Implement POST /api/users endpoint with validation and persistence to SQLite."]
</task>

<context>
[All relevant context: files to modify, existing APIs, database schema, constraints from previous tasks, acceptance criteria. Be specific — include file paths, function names, table names.]
</context>

<format>
[Specify the expected output format: "A single Python file at backend/app/routers/users.py", "A git commit with message...", "A test file with N test cases", etc.]
</format>

<constraints>
[Non-negotiable rules: tech stack limits, coding standards, what NOT to do, max lines, must-pass tests, etc.]
</constraints>