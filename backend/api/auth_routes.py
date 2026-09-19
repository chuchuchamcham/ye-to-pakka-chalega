"""Login, session and user-management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from backend.api.auth import (
    ADMIN, AUDITOR, OPERATOR, ROLES, TOKEN_TTL_SEC, User, authenticate, create_user,
    current_user, has_users, issue_token, list_users, require_role,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=256)
    role: str = Field(default=OPERATOR)


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "bw_session", token,
        max_age=TOKEN_TTL_SEC,
        httponly=True,       # not readable by scripts, so XSS cannot lift it
        samesite="lax",
        # Not forced secure: the edge deployment is often plain http on a
        # closed LAN, and a cookie marked secure would simply never be sent.
        secure=False,
        path="/",
    )


@router.get("/me")
def whoami(request: Request) -> dict:
    """Session state. Deliberately unauthenticated so the UI can tell the
    difference between 'logged out' and 'not set up yet' before showing a form."""
    from backend.api.auth import _token_from, decode_token

    if not has_users():
        return {"configured": False, "authenticated": False, "user": None}
    token = _token_from(request)
    user = decode_token(token) if token else None
    if user is None:
        return {"configured": True, "authenticated": False, "user": None}
    return {"configured": True, "authenticated": True,
            "user": {"username": user.username, "role": user.role}}


@router.post("/bootstrap", status_code=201)
def bootstrap_admin(req: CreateUserRequest, response: Response) -> dict:
    """Create the first administrator.

    Only available while no account exists, so it cannot be used later to mint
    an admin on a running system.
    """
    if has_users():
        raise HTTPException(409, "already configured - sign in instead")
    try:
        user = create_user(req.username, req.password, ADMIN)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    token = issue_token(user)
    _set_session_cookie(response, token)
    return {"token": token, "user": {"username": user.username, "role": user.role}}


@router.post("/login")
def login(req: LoginRequest, response: Response) -> dict:
    user = authenticate(req.username, req.password)
    if user is None:
        # One message for both failure modes, so it cannot be used to discover
        # which usernames are valid.
        raise HTTPException(401, "invalid username or password")
    token = issue_token(user)
    _set_session_cookie(response, token)
    return {"token": token, "user": {"username": user.username, "role": user.role}}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie("bw_session", path="/")
    return {"ok": True}


@router.get("/users")
def get_users(_: User = Depends(require_role(ADMIN))) -> list[dict]:
    return [{"username": u.username, "role": u.role} for u in list_users()]


@router.post("/users", status_code=201)
def add_user(req: CreateUserRequest, _: User = Depends(require_role(ADMIN))) -> dict:
    if req.role not in ROLES:
        raise HTTPException(400, f"role must be one of: {', '.join(ROLES)}")
    try:
        user = create_user(req.username, req.password, req.role)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"username": user.username, "role": user.role}


@router.get("/roles")
def roles() -> dict:
    return {
        "roles": [
            {"role": ADMIN, "description": "Full control, including cameras, users and deletion"},
            {"role": OPERATOR, "description": "Monitor and configure analysis; cannot delete records"},
            {"role": AUDITOR, "description": "Read-only, including the audit trail"},
        ],
    }
