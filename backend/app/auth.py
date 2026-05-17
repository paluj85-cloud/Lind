"""Auth module — bcrypt password hashing, validation, token generation."""

from __future__ import annotations

import re
import uuid

import bcrypt


BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """Hash a password with bcrypt, return the hash string."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def validate_login(login: str) -> str | None:
    """Return an error message if login is invalid, or None if valid."""
    if not login or not isinstance(login, str):
        return "Логин обязателен"
    login = login.strip()
    if len(login) < 3:
        return "Логин должен быть не менее 3 символов"
    if len(login) > 30:
        return "Логин должен быть не более 30 символов"
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ0-9_\-]+$", login):
        return "Логин может содержать только буквы, цифры, дефис и подчёркивание"
    return None


def validate_password(password: str) -> str | None:
    """Return an error message if password is invalid, or None if valid."""
    if not password or not isinstance(password, str):
        return "Пароль обязателен"
    if len(password) < 4:
        return "Пароль должен быть не менее 4 символов"
    if len(password) > 128:
        return "Пароль слишком длинный"
    return None


def generate_token() -> str:
    """Generate a new auth token (UUID4)."""
    return str(uuid.uuid4())