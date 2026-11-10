"""
Shared route dependencies.

The only trusted identity is the user returned by Nest /auth/validate, which AuthMiddleware
stores on request.state.user as {"valid": true, "user": {"id", "email", "name", "isAdmin"}}.
Any userId sent by the client (body or query) is ignored.
"""
from dataclasses import dataclass

from fastapi import HTTPException, Request


@dataclass(frozen=True)
class CurrentUser:
    id: int
    email: str
    name: str
    is_admin: bool

    @property
    def id_str(self) -> str:
        """user_id columns in the RAG tables are strings."""
        return str(self.id)


def get_current_user(request: Request) -> CurrentUser:
    payload = getattr(request.state, "user", None) or {}
    user = payload.get("user", payload) if isinstance(payload, dict) else {}
    user_id = user.get("id") if isinstance(user, dict) else None

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise HTTPException(status_code=401, detail="Authenticated user not found")

    return CurrentUser(
        id=user_id,
        email=user.get("email") or "",
        name=user.get("name") or "",
        is_admin=bool(user.get("isAdmin", False)),
    )
