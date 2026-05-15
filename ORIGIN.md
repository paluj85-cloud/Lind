# ORIGIN.md — Project Context

## Project Name
Lind (ADND) — AI-Powered Tabletop RPG Engine

## Purpose
Web-приложение для игры в настольную ролевую игру (D&D-подобную), где роль Мастера (Game Master) исполняет AI (Экс-Ис), а игрок взаимодействует через веб-интерфейс. AI создаёт миры, проводит игровые сессии, ведёт нарратив. База знаний: adnd-knowledge/, исходные чаты: chat_deepseek/ (115 сессий).

## Tech Stack
- Python 3.11+
- FastAPI + Uvicorn
- SQLite with FTS5
- Vanilla HTML/CSS/JS
- DeepSeek API (deepseek-v4-flash for app, deepseek-v4-pro for architect)
- pytest, httpx, pytest-asyncio

## Infrastructure
- Dev: local machine, port 8001
- Prod: VPS Hostland, Nginx, systemd

## Key Decisions
- AI-мастер: Экс-Ис (exis-master) — основной промт, ведущий игру
- AI-помощник: Анима (anima-assistant) — искра души, внутренний голос
- База знаний: adnd-knowledge/ — AI-читаемая структура (12 разделов)
- Исходные данные: chat_deepseek/ — 115 экспортированных чатов с DeepSeek (2026-04-15 по 2026-05-15)
- Технические спецификации: v0.1 (одиночная игра), v0.2 (мультиплеер)

## Evolution
See `project_memory/CHANGELOG.md` for full history.