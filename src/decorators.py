from functools import wraps

from flask import jsonify, request, g

from src.database import SessionLocal
from src.services.auth_service import get_user_from_session


SESSION_COOKIE_NAME = "session_token"


def login_required(func):
    """
    Protects a Flask route by requiring a valid authenticated session.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.cookies.get(SESSION_COOKIE_NAME)

        if not token:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401

        db = SessionLocal()

        try:
            user = get_user_from_session(
                db=db,
                token=token
            )

            if user is None:
                return jsonify({
                    "success": False,
                    "message": "Invalid or expired session"
                }), 401

            g.current_user = user

            return func(*args, **kwargs)

        finally:
            db.close()

    return wrapper