from flask import Blueprint, jsonify, request, make_response

from src.database import SessionLocal
from src.services.auth_service import (
    authenticate_user,
    create_session,
    get_user_from_session,
    revoke_session,
)


auth_bp = Blueprint(
    "authentication",
    __name__,
    url_prefix="/auth"
)

SESSION_COOKIE_NAME = "session_token"


@auth_bp.post("/login")
def login():
    """
    Authenticates a user using their name and access key.

    If successful:
    - creates a persistent session
    - stores the session token in an HTTP-only cookie
    """

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "Missing request body"
        }), 400

    name = data.get("name", "").strip()
    access_key = data.get("access_key", "")

    if not name or not access_key:
        return jsonify({
            "success": False,
            "message": "Name and access key are required"
        }), 400

    db = SessionLocal()

    try:
        user = authenticate_user(
            db=db,
            name=name,
            access_key=access_key
        )

        if user is None:
            return jsonify({
                "success": False,
                "message": "Invalid name or access key"
            }), 401

        session_token = create_session(
            db=db,
            user=user
        )

        response = make_response(
            jsonify({
                "success": True,
                "message": "Authentication successful",
                "user": {
                    "user_id": user.user_id,
                    "name": user.name
                }
            }),
            200
        )

        response.set_cookie(
            SESSION_COOKIE_NAME,
            session_token,
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=60 * 60 * 24 * 90
        )

        return response

    finally:
        db.close()


@auth_bp.post("/logout")
def logout():
    """
    Revokes the current user's session and removes
    the authentication cookie.
    """

    token = request.cookies.get(SESSION_COOKIE_NAME)

    db = SessionLocal()

    try:
        if token:
            revoke_session(
                db=db,
                token=token
            )

        response = make_response(
            jsonify({
                "success": True,
                "message": "Logged out successfully"
            }),
            200
        )

        response.delete_cookie(
            SESSION_COOKIE_NAME,
            httponly=True,
            secure=False,
            samesite="Lax"
        )

        return response

    finally:
        db.close()


@auth_bp.get("/status")
def status():
    """
    Checks whether the current browser has a valid session.
    """

    token = request.cookies.get(SESSION_COOKIE_NAME)

    if not token:
        return jsonify({
            "authenticated": False
        }), 401

    db = SessionLocal()

    try:
        user = get_user_from_session(
            db=db,
            token=token
        )

        if user is None:
            return jsonify({
                "authenticated": False
            }), 401

        return jsonify({
            "authenticated": True,
            "user": {
                "user_id": user.user_id,
                "name": user.name
            }
        }), 200

    finally:
        db.close()