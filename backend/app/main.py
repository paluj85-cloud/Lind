"""Lind ADND Game Server — FastAPI + WebSocket + Game Loop."""

from __future__ import annotations

import json
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings, ensure_directories
from backend.app.db import get_db, close_db, create_session, update_session_player, save_message, get_session
from backend.app.game.loop import GameLoop
from backend.app.game.logger import get_game_logger
from backend.app.admin.routes import router as admin_router

# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="Lind ADND Engine", version="0.1.0")

# Mount static files (player + admin frontend)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Mount admin API routes
app.include_router(admin_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# Serve player index.html at /
@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse("backend/static/index.html")


# Serve admin.html at /admin
@app.get("/admin")
async def admin_panel():
    from fastapi.responses import FileResponse
    return FileResponse("backend/static/admin.html")


# ── Startup / Shutdown ──────────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    """Initialise DB, directories, logger on startup."""
    ensure_directories()
    await get_db()  # Initialise DB and run schema
    get_game_logger().info("Lind server started")


@app.on_event("shutdown")
async def shutdown():
    """Close DB connection on shutdown."""
    await close_db()
    get_game_logger().info("Lind server stopped")


# ── WebSocket ───────────────────────────────────────────────────────────────


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Main game WebSocket endpoint.

    Protocol (client → server):
      - {"type": "player_join", "player_name": "..."}
      - {"type": "player_say", "content": "..."}
      - {"type": "dice_result", "request_id": "...", "roll": N, "modifier": M}

    Protocol (server → client):
      - {"type": "session_created", "session_id": "..."}
      - {"type": "master_thinking", "status": "started|stopped"}
      - {"type": "master_speech", "narrator": "...", "dice_request": {...}}
    """
    await ws.accept()

    # Create session immediately on connect
    session_id = str(uuid4())
    session_created = False  # Track if we need to send session_created
    loop: GameLoop | None = None

    game_log = get_game_logger(session_id)
    game_log.info("WebSocket connected, tentative_session=%s", session_id)

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "detail": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            if not session_created and msg_type != "player_join":
                # First message must be player_join — ignore until we get it
                await ws.send_json({"type": "error", "detail": "Send player_join first"})
                continue

            if msg_type == "player_join":
                player_name = msg.get("player_name", "Неизвестный")
                existing_sid = msg.get("session_id", "")

                if existing_sid:
                    # Check if this session exists and is active
                    existing_session = await get_session(existing_sid)
                    if existing_session and existing_session.get("status") == "active":
                        # Restore existing session instead of creating new one
                        session_id = existing_sid
                        game_log = get_game_logger(session_id)
                        game_log.info("Restoring existing session for: %s", player_name)

                        loop = GameLoop(session_id=session_id, ws=ws, game_log=game_log)
                        await update_session_player(session_id, player_name)
                        await save_message(session_id, "player", "say", f"[Вернулся в игру как {player_name}]")
                        await loop.restore_session(player_name)
                        session_created = True
                        continue

                # New session (no existing session_id, or session expired)
                if not session_created:
                    await create_session(session_id, world_name="Lind")
                    await ws.send_json({"type": "session_created", "session_id": session_id})
                    session_created = True

                game_log = get_game_logger(session_id)
                loop = GameLoop(session_id=session_id, ws=ws, game_log=game_log)

                await update_session_player(session_id, player_name)
                await save_message(session_id, "player", "say", f"[Присоединился к игре как {player_name}]")
                game_log.info("Player joined: %s", player_name)
                await loop.start_greeting(player_name)

            elif msg_type == "player_say":
                # Player sends an action/message
                content = msg.get("content", "")
                if content.strip():
                    await save_message(session_id, "player", "say", content)
                    game_log.info("Player says: %s", content[:100])
                    await loop.handle_player_input(content)

            elif msg_type == "dice_result":
                # Player rolled the dice — second LLM pass
                request_id = msg.get("request_id", "")
                roll = msg.get("roll", 0)
                modifier = msg.get("modifier", 0)
                game_log.info("Dice result: request_id=%s roll=%d modifier=%d", request_id, roll, modifier)
                await loop.handle_dice_result(request_id, roll, modifier)

            else:
                await ws.send_json({"type": "error", "detail": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        game_log.info("WebSocket disconnected, session=%s", session_id)
    except Exception as exc:
        game_log.error("WebSocket error: %s", str(exc))
        try:
            await ws.close(code=1011, reason="Internal error")
        except Exception:
            pass


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )