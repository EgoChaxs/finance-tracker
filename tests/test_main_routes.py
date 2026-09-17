def test_index_redirects_to_login_without_session(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_login_page_is_served_without_session(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b"html" in response.data.lower()


def test_authenticated_login_page_redirects_to_index(authenticated_client):
    response = authenticated_client.get("/login")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_authenticated_index_serves_app(authenticated_client):
    response = authenticated_client.get("/")

    assert response.status_code == 200
    assert b"html" in response.data.lower()
