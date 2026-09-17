from src.models import SessionModel


def test_login_rejects_missing_body(client):
    response = client.post("/auth/login")

    assert response.status_code == 400
    assert response.get_json() == {
        "success": False,
        "message": "Missing request body",
    }


def test_login_rejects_missing_credentials(client):
    response = client.post("/auth/login", json={"name": "Alice"})

    assert response.status_code == 400
    assert response.get_json()["message"] == "Name and access key are required"


def test_login_rejects_invalid_credentials(client, user):
    response = client.post(
        "/auth/login",
        json={"name": user.name, "access_key": "wrong-key"},
    )

    assert response.status_code == 401
    assert response.get_json() == {
        "success": False,
        "message": "Invalid name or access key",
    }


def test_login_sets_session_and_status_returns_user(client, user, db):
    response = client.post(
        "/auth/login",
        json={"name": "  Alice  ", "access_key": "alice-secret"},
    )

    assert response.status_code == 200
    assert response.get_json()["user"] == {
        "user_id": user.user_id,
        "name": "Alice",
    }
    assert "session_token=" in response.headers["Set-Cookie"]
    assert "HttpOnly" in response.headers["Set-Cookie"]

    status_response = client.get("/auth/status")
    assert status_response.status_code == 200
    assert status_response.get_json()["authenticated"] is True
    assert status_response.get_json()["user"]["user_id"] == user.user_id

    db.expire_all()
    assert db.query(SessionModel).count() == 1


def test_status_rejects_missing_or_invalid_session(client):
    missing = client.get("/auth/status")
    assert missing.status_code == 401
    assert missing.get_json() == {"authenticated": False}

    client.set_cookie("session_token", "not-a-real-session")
    invalid = client.get("/auth/status")
    assert invalid.status_code == 401
    assert invalid.get_json() == {"authenticated": False}


def test_logout_revokes_session_and_clears_cookie(client, user, db):
    login = client.post(
        "/auth/login",
        json={"name": user.name, "access_key": "alice-secret"},
    )
    assert login.status_code == 200

    response = client.post("/auth/logout")

    assert response.status_code == 200
    assert response.get_json()["message"] == "Logged out successfully"
    assert "session_token=;" in response.headers["Set-Cookie"]

    db.expire_all()
    assert db.query(SessionModel).count() == 0
    assert client.get("/auth/status").status_code == 401


def test_logout_without_session_is_still_successful(client):
    response = client.post("/auth/logout")

    assert response.status_code == 200
    assert response.get_json()["success"] is True
