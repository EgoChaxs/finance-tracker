# src/services/auth_service.py

import hashlib
import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.orm import Session

from src.models import UserModel, SessionModel


password_hasher = PasswordHasher()

SESSION_LIFETIME_DAYS = 90


def hash_access_key(access_key: str) -> str:
    """
    Hashes an access key before storing it in the database.
    """
    return password_hasher.hash(access_key)


def verify_access_key(access_key: str, hashed_access_key: str) -> bool:
    """
    Verifies a plaintext access key against its stored Argon2 hash.
    """
    try:
        return password_hasher.verify(
            hashed_access_key,
            access_key
        )
    except VerifyMismatchError:
        return False


def authenticate_user(
    db: Session,
    name: str,
    access_key: str
) -> UserModel | None:
    """
    Authenticates a user using their name and access key.

    Returns the user if authentication succeeds.
    Returns None otherwise.
    """

    user = (
        db.query(UserModel)
        .filter(UserModel.name == name)
        .first()
    )

    if user is None:
        return None

    if not verify_access_key(
        access_key,
        user.hashed_access_key
    ):
        return None

    return user


def _hash_session_token(token: str) -> str:
    """
    Hashes a session token before storing it in the database.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(
    db: Session,
    user: UserModel
) -> str:
    """
    Creates a persistent session for a user.

    Returns the raw session token that should be placed
    inside the browser's cookie.
    """

    token = secrets.token_urlsafe(32)
    token_hash = _hash_session_token(token)

    now = datetime.now()

    session = SessionModel(
        user_id=user.user_id,
        session_identifier=token_hash,
        created_at=now,
        expires_at=now + timedelta(
            days=SESSION_LIFETIME_DAYS
        )
    )

    db.add(session)
    db.commit()

    return token


def get_user_from_session(
    db: Session,
    token: str
) -> UserModel | None:
    """
    Returns the user associated with a valid session token.

    Returns None if the session does not exist or has expired.
    """

    if not token:
        return None

    token_hash = _hash_session_token(token)

    session = (
        db.query(SessionModel)
        .filter(
            SessionModel.session_identifier == token_hash
        )
        .first()
    )

    if session is None:
        return None

    if session.expires_at <= datetime.now():
        db.delete(session)
        db.commit()
        return None

    return session.user


def revoke_session(
    db: Session,
    token: str
) -> bool:
    """
    Deletes a session from the database.

    Returns True if a session was deleted.
    Returns False if no matching session existed.
    """

    if not token:
        return False

    token_hash = _hash_session_token(token)

    session = (
        db.query(SessionModel)
        .filter(
            SessionModel.session_identifier == token_hash
        )
        .first()
    )

    if session is None:
        return False

    db.delete(session)
    db.commit()

    return True