def test_login_required_rejects_missing_cookie(client):
    response = client.get("/api/categories")

    assert response.status_code == 401
    assert response.get_json() == {
        "success": False,
        "message": "Authentication required",
    }


def test_login_required_rejects_invalid_cookie(client):
    client.set_cookie("session_token", "invalid-session-token")

    response = client.get("/api/categories")

    assert response.status_code == 401
    assert response.get_json() == {
        "success": False,
        "message": "Invalid or expired session",
    }
