"""Magic link authentication for SaaS dashboard.

Lightweight auth using itsdangerous for signing and JWT-style cookies.
No passwords, no heavy auth libraries.
"""

import secrets
import time
from typing import Optional, Callable
from functools import wraps

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, HTTPException, Response
from fastapi.responses import RedirectResponse

# Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, load from env
serializer = URLSafeTimedSerializer(SECRET_KEY)
SESSION_COOKIE_NAME = "drip_session"
SESSION_MAX_AGE = 86400 * 7  # 7 days
MAGIC_LINK_EXPIRY = 900  # 15 minutes


def generate_magic_token(email: str) -> str:
    """Generate a magic link token for email verification."""
    return secrets.token_urlsafe(32)


def create_session_token(email: str, account_id: str) -> str:
    """Create a signed session token."""
    return serializer.dumps({
        "email": email,
        "account_id": account_id,
        "created": int(time.time()),
    })


def verify_session_token(token: str) -> Optional[dict]:
    """Verify a session token and return payload."""
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data
    except (BadSignature, SignatureExpired):
        return None


def get_current_user(request: Request) -> Optional[dict]:
    """Extract user from session cookie."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    return verify_session_token(token)


def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication for a route."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = get_current_user(request)
        if not user:
            return RedirectResponse(url="/signup", status_code=302)

        # Add user to request state
        request.state.user = user
        return await func(request, *args, **kwargs)
    return wrapper


def set_session_cookie(response: Response, email: str, account_id: str):
    """Set the session cookie on a response."""
    token = create_session_token(email, account_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response):
    """Clear the session cookie (logout)."""
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


def generate_account_id() -> str:
    """Generate a unique account ID."""
    return f"acct_{secrets.token_hex(8)}"
