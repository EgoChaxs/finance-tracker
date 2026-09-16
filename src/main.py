from flask import Flask, redirect, send_from_directory, request
from pathlib import Path

from src.api.authentication import auth_bp
from src.api.transactions import transactions_bp
from src.api.category import categories_bp
from src.api.budget import budgets_bp
from src.api.goals import goals_bp
from src.database import SessionLocal
from src.services.auth_service import get_user_from_session


BASE_DIR = Path(__file__).resolve().parent.parent

AUTH_FRONTEND_DIR = BASE_DIR / "frontend" / "auth"
APP_FRONTEND_DIR = BASE_DIR / "frontend" / "app"


app = Flask(__name__)

app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(budgets_bp)
app.register_blueprint(goals_bp)


SESSION_COOKIE_NAME = "session_token"


@app.get("/login")
def login_page():
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if token:
        db = SessionLocal()

        try:
            user = get_user_from_session(
                db=db,
                token=token
            )

            if user is not None:
                return redirect("/")

        finally:
            db.close()

    return send_from_directory(
        AUTH_FRONTEND_DIR,
        "login.html"
    )


@app.get("/login/<path:filename>")
def login_assets(filename):
    return send_from_directory(
        AUTH_FRONTEND_DIR,
        filename
    )


@app.get("/")
def index():
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if not token:
        return redirect("/login")

    db = SessionLocal()

    try:
        user = get_user_from_session(
            db=db,
            token=token
        )

        if user is None:
            return redirect("/login")

    finally:
        db.close()

    return send_from_directory(
        APP_FRONTEND_DIR,
        "index.html"
    )


@app.get("/app/<path:filename>")
def app_assets(filename):
    return send_from_directory(
        APP_FRONTEND_DIR,
        filename
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )