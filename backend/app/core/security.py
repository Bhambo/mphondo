"""JWT verification against Supabase GoTrue secret.

FastAPI routes that require authentication use `CurrentUser` from deps.py.
This module only handles token decoding — never token issuance (Supabase owns that).
"""

from typing import Any
import uuid

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"


def decode_supabase_token(token: str) -> dict[str, Any]:
    """Decode and verify a Supabase JWT. Raises JWTError on failure."""
    return jwt.decode(
        token,
        settings.SUPABASE_JWT_SECRET,
        algorithms=[ALGORITHM],
        options={"verify_aud": False},  # Supabase omits standard aud claim
    )


def extract_user_id(token: str) -> uuid.UUID:
    payload = decode_supabase_token(token)
    sub = payload.get("sub")
    if not sub:
        raise JWTError("Token missing sub claim")
    return uuid.UUID(sub)
