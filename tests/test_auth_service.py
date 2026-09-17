from datetime import datetime, timedelta

from src.models import SessionModel
from src.services.auth_service import (
    authenticate_user,
    create_session,
    get_user_from_session,
    hash_access_key,
    revoke_session,
    verify_access_key,
)


def test_hash_and_verify_access_key():
    hashed = hash_access_key("super-secret")

    assert hashed != "super-secret"
    assert verify_access_key("super-secret", hashed) is True
    assert verify_access_key("wrong", hashed) is False


def test_authenticate_user(db, user_factory):
    user = user_factory("Alice", "correct-key")

    assert authenticate_user(db, "Alice", "correct-key").user_id == user.user_id
    assert authenticate_user(db, "Alice", "wrong-key") is None
    assert authenticate_user(db, "Nobody", "correct-key") is None


def test_create_and_resolve_session(db, user_factory):
    user = user_factory()

    token = create_session(db, user)
    session = db.query(SessionModel).one()

    assert token
    assert session.session_identifier != token
    assert get_user_from_session(db, token).user_id == user.user_id


def test_expired_session_is_rejected_and_deleted(db, user_factory):
    user = user_factory()
    token = create_session(db, user)
    session = db.query(SessionModel).one()
    session.expires_at = datetime.now() - timedelta(seconds=1)
    db.commit()

    assert get_user_from_session(db, token) is None
    assert db.query(SessionModel).count() == 0


def test_revoke_session(db, user_factory):
    user = user_factory()
    token = create_session(db, user)

    assert revoke_session(db, token) is True
    assert get_user_from_session(db, token) is None
    assert revoke_session(db, token) is False
