"""Simple local auth for demo. Passwords hashed; tokens stored server-side."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path
from typing import Any

from app.config import Settings


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()


class AuthStore:
    def __init__(self, settings: Settings) -> None:
        self.path = Path(settings.data_dir) / "users.json"
        self.sessions_path = Path(settings.data_dir) / "sessions.json"
        self.ttl = settings.session_ttl_hours * 3600
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(self.path, {"users": []})
        if not self.sessions_path.exists():
            self._write(self.sessions_path, {"sessions": {}})

    def _read(self, path: Path) -> dict[str, Any]:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            # Empty file (e.g. manually cleared) — reset to a valid envelope
            if path == self.path:
                data: dict[str, Any] = {"users": []}
            else:
                data = {"sessions": {}}
            self._write(path, data)
            return data
        return json.loads(raw)

    def _write(self, path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def register(self, email: str, password: str, name: str) -> dict[str, Any]:
        email = email.strip().lower()
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        data = self._read(self.path)
        if any(u["email"] == email for u in data["users"]):
            raise ValueError("Email already registered")
        salt = secrets.token_hex(8)
        user = {
            "id": secrets.token_hex(8),
            "email": email,
            "name": name.strip() or email.split("@")[0],
            "salt": salt,
            "password_hash": _hash_password(password, salt),
            "cloud": None,
            "gcp_project_id": None,
        }
        data["users"].append(user)
        self._write(self.path, data)
        return {"id": user["id"], "email": user["email"], "name": user["name"]}

    def login(self, email: str, password: str) -> tuple[str, dict[str, Any]]:
        email = email.strip().lower()
        data = self._read(self.path)
        user = next((u for u in data["users"] if u["email"] == email), None)
        if not user:
            raise ValueError("Invalid email or password")
        digest = _hash_password(password, user["salt"])
        if not hmac.compare_digest(digest, user["password_hash"]):
            raise ValueError("Invalid email or password")
        token = secrets.token_urlsafe(32)
        sessions = self._read(self.sessions_path)
        sessions["sessions"][token] = {
            "user_id": user["id"],
            "expires_at": time.time() + self.ttl,
        }
        self._write(self.sessions_path, sessions)
        return token, {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "cloud": user.get("cloud"),
            "gcp_project_id": user.get("gcp_project_id"),
        }

    def logout(self, token: str) -> None:
        sessions = self._read(self.sessions_path)
        sessions["sessions"].pop(token, None)
        self._write(self.sessions_path, sessions)

    def user_from_token(self, token: str | None) -> dict[str, Any] | None:
        if not token:
            return None
        sessions = self._read(self.sessions_path)
        sess = sessions["sessions"].get(token)
        if not sess or sess["expires_at"] < time.time():
            if sess:
                sessions["sessions"].pop(token, None)
                self._write(self.sessions_path, sessions)
            return None
        data = self._read(self.path)
        user = next((u for u in data["users"] if u["id"] == sess["user_id"]), None)
        if not user:
            return None
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "cloud": user.get("cloud"),
            "gcp_project_id": user.get("gcp_project_id"),
        }

    def update_cloud(self, user_id: str, cloud: str, gcp_project_id: str) -> dict[str, Any]:
        data = self._read(self.path)
        for user in data["users"]:
            if user["id"] == user_id:
                user["cloud"] = cloud
                user["gcp_project_id"] = gcp_project_id
                self._write(self.path, data)
                return {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "cloud": user["cloud"],
                    "gcp_project_id": user["gcp_project_id"],
                }
        raise ValueError("User not found")