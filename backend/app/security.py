from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.config import settings

_hasher = PasswordHasher()

# A fake hash used when the email does not exist, so that "wrong email" and
# "wrong password" take the same time and an attacker cannot tell them apart.
DUMMY_HASH = _hasher.hash("this-is-not-a-real-password")


def hash_password(password: str) -> str:
    """Scrambles a password. The result (not the password) goes in the database."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def check_password_strength(password: str) -> str | None:
    """Returns a message if the password is too weak, or None if it is fine."""
    if len(password) < 10:
        return "Password must be at least 10 characters long."
    if not any(c.islower() for c in password):
        return "Password needs at least one small letter."
    if not any(c.isupper() for c in password):
        return "Password needs at least one capital letter."
    if not any(c.isdigit() for c in password):
        return "Password needs at least one number."
    return None


def create_token(employee_id: int) -> str:
    """A signed 'ticket' that proves the person logged in. It expires."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(employee_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.token_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def read_token(token: str) -> int | None:
    """Returns the employee id if the ticket is real and not expired, else None."""
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return int(data["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None