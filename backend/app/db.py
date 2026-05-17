"""Database layer — SQLite with FTS5, async via aiosqlite."""

from __future__ import annotations

import aiosqlite

from backend.app.config import settings
from backend.app.models import utc_now


DB: aiosqlite.Connection | None = None


SCHEMA_SQL = """
-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    world_name TEXT DEFAULT 'Lind',
    player_name TEXT DEFAULT '',
    reveal_level INTEGER DEFAULT 0
);

-- Messages (chat history)
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    role TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- World facts (Явленный Свиток)
CREATE TABLE IF NOT EXISTS world_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    fact_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ABSOLUTE_TRUTH',
    summary TEXT NOT NULL,
    details TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- FTS5 index for world_facts
CREATE VIRTUAL TABLE IF NOT EXISTS world_facts_fts USING fts5(
    summary, details,
    content='world_facts',
    content_rowid='id'
);

-- LLM traces (full prompt-response logging)
CREATE TABLE IF NOT EXISTS llm_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    call_type TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    user_context TEXT NOT NULL,
    response_raw TEXT NOT NULL,
    response_parsed TEXT DEFAULT '',
    duration_ms INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_llm_traces_session ON llm_traces(session_id, sequence);
CREATE INDEX IF NOT EXISTS idx_world_facts_session ON world_facts(session_id);
CREATE INDEX IF NOT EXISTS idx_world_facts_status ON world_facts(status);

-- Triggers for FTS5
CREATE TRIGGER IF NOT EXISTS world_facts_ai AFTER INSERT ON world_facts BEGIN
    INSERT INTO world_facts_fts(rowid, summary, details)
    VALUES (new.id, new.summary, new.details);
END;

CREATE TRIGGER IF NOT EXISTS world_facts_ad AFTER DELETE ON world_facts BEGIN
    INSERT INTO world_facts_fts(world_facts_fts, rowid, summary, details)
    VALUES ('delete', old.id, old.summary, old.details);
END;

CREATE TRIGGER IF NOT EXISTS world_facts_au AFTER UPDATE ON world_facts BEGIN
    INSERT INTO world_facts_fts(world_facts_fts, rowid, summary, details)
    VALUES ('delete', old.id, old.summary, old.details);
    INSERT INTO world_facts_fts(rowid, summary, details)
    VALUES (new.id, new.summary, new.details);
END;
"""


async def get_db() -> aiosqlite.Connection:
    """Get or initialise the database connection."""
    global DB
    if DB is None:
        DB = await aiosqlite.connect(settings.DATABASE_PATH)
        DB.row_factory = aiosqlite.Row
        await DB.executescript(SCHEMA_SQL)
        await DB.commit()
        # Enable WAL mode for better concurrency
        await DB.execute("PRAGMA journal_mode=WAL")
        await DB.execute("PRAGMA foreign_keys=ON")
    return DB


async def close_db() -> None:
    """Close the database connection."""
    global DB
    if DB is not None:
        await DB.close()
        DB = None


# ── Session operations ──────────────────────────────────────────────────────


async def create_session(
    session_id: str,
    world_name: str = "Lind",
    player_name: str = "",
) -> dict:
    """Create a new game session."""
    db = await get_db()
    now = utc_now()
    await db.execute(
        """INSERT INTO sessions (id, created_at, status, world_name, player_name)
           VALUES (?, ?, 'active', ?, ?)""",
        (session_id, now, world_name, player_name),
    )
    await db.commit()
    return {
        "id": session_id,
        "created_at": now,
        "status": "active",
        "world_name": world_name,
        "player_name": player_name,
    }


async def get_session(session_id: str) -> dict | None:
    """Get a session by ID."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM sessions WHERE id = ?", (session_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_session_player(session_id: str, player_name: str) -> None:
    """Update the player's name in a session."""
    db = await get_db()
    await db.execute(
        "UPDATE sessions SET player_name = ? WHERE id = ?",
        (player_name, session_id),
    )
    await db.commit()


async def finish_session(session_id: str) -> None:
    """Mark a session as finished."""
    db = await get_db()
    await db.execute(
        "UPDATE sessions SET status = 'finished' WHERE id = ?",
        (session_id,),
    )
    await db.commit()


async def list_sessions() -> list[dict]:
    """List all sessions, newest first."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT s.*, 
                  (SELECT COUNT(*) FROM messages WHERE session_id = s.id) as message_count,
                  (SELECT COUNT(*) FROM llm_traces WHERE session_id = s.id) as trace_count
           FROM sessions s
           ORDER BY s.created_at DESC"""
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# ── Message operations ──────────────────────────────────────────────────────


async def save_message(
    session_id: str,
    role: str,
    msg_type: str,
    content: str,
) -> int:
    """Save a chat message and return its ID."""
    db = await get_db()
    now = utc_now()
    cursor = await db.execute(
        """INSERT INTO messages (session_id, timestamp, role, type, content)
           VALUES (?, ?, ?, ?, ?)""",
        (session_id, now, role, msg_type, content),
    )
    await db.commit()
    return cursor.lastrowid


async def get_recent_messages(
    session_id: str, limit: int = 20
) -> list[dict]:
    """Get the N most recent messages from a session (excludes system messages)."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM messages
           WHERE session_id = ?
             AND role != 'system'
           ORDER BY id DESC
           LIMIT ?""",
        (session_id, limit),
    )
    rows = await cursor.fetchall()
    # Reverse to chronological order
    messages = [dict(r) for r in rows]
    messages.reverse()
    return messages


async def get_all_messages(session_id: str) -> list[dict]:
    """Get all messages from a session in chronological order."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM messages
           WHERE session_id = ?
           ORDER BY id ASC""",
        (session_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# ── World facts operations ──────────────────────────────────────────────────


async def save_world_fact(
    session_id: str,
    fact_type: str,
    status: str,
    summary: str,
    details: str = "{}",
) -> int:
    """Save a world fact and return its ID."""
    db = await get_db()
    now = utc_now()
    cursor = await db.execute(
        """INSERT INTO world_facts (session_id, fact_type, status, summary, details, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (session_id, fact_type, status, summary, details, now),
    )
    await db.commit()
    return cursor.lastrowid


async def get_world_facts(
    session_id: str, status_filter: str | None = None
) -> list[dict]:
    """Get all world facts for a session, optionally filtered by status."""
    db = await get_db()
    if status_filter:
        cursor = await db.execute(
            """SELECT * FROM world_facts
               WHERE session_id = ? AND status = ?
               ORDER BY id ASC""",
            (session_id, status_filter),
        )
    else:
        cursor = await db.execute(
            """SELECT * FROM world_facts
               WHERE session_id = ?
               ORDER BY id ASC""",
            (session_id,),
        )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def search_world_facts(
    session_id: str, query: str, limit: int = 5
) -> list[dict]:
    """Full-text search in world facts using FTS5."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT wf.* FROM world_facts wf
           JOIN world_facts_fts fts ON wf.id = fts.rowid
           WHERE wf.session_id = ? AND world_facts_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (session_id, query, limit),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# ── LLM trace operations ────────────────────────────────────────────────────


async def save_llm_trace(
    session_id: str,
    sequence: int,
    call_type: str,
    system_prompt: str,
    user_context: str,
    response_raw: str,
    response_parsed: str = "",
    duration_ms: int = 0,
    token_count: int = 0,
) -> int:
    """Save an LLM call trace and return its ID."""
    db = await get_db()
    now = utc_now()
    cursor = await db.execute(
        """INSERT INTO llm_traces
           (session_id, sequence, call_type, system_prompt, user_context,
            response_raw, response_parsed, duration_ms, token_count, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id, sequence, call_type, system_prompt, user_context,
            response_raw, response_parsed, duration_ms, token_count, now,
        ),
    )
    await db.commit()
    return cursor.lastrowid


async def get_llm_traces(session_id: str) -> list[dict]:
    """Get all LLM traces for a session."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM llm_traces
           WHERE session_id = ?
           ORDER BY sequence ASC""",
        (session_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_llm_trace(trace_id: int) -> dict | None:
    """Get a single LLM trace by ID."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM llm_traces WHERE id = ?", (trace_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_next_sequence(session_id: str) -> int:
    """Get the next sequence number for a session's LLM calls."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT COALESCE(MAX(sequence), 0) + 1 FROM llm_traces WHERE session_id = ?",
        (session_id,),
    )
    row = await cursor.fetchone()
    return row[0] if row else 1