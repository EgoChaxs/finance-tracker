import pytest

from src.models import CategoryModel


def test_get_categories_returns_only_current_users_categories(
    authenticated_client,
    user,
    second_user,
    category_factory,
):
    own_b = category_factory(user, name="Utilities")
    own_a = category_factory(user, name="Food")
    category_factory(second_user, name="Private Bob Category")

    response = authenticated_client.get("/api/categories")

    assert response.status_code == 200
    categories = response.get_json()["categories"]
    assert [item["category_id"] for item in categories] == [
        own_a.category_id,
        own_b.category_id,
    ]
    assert [item["name"] for item in categories] == ["Food", "Utilities"]


def test_get_category_hides_another_users_category(
    authenticated_client,
    second_user,
    category_factory,
):
    other = category_factory(second_user)

    response = authenticated_client.get(f"/api/categories/{other.category_id}")

    assert response.status_code == 404
    assert response.get_json()["message"] == "Category not found"


def test_create_category_trims_and_normalizes_optional_fields(
    authenticated_client,
    user,
    db,
):
    response = authenticated_client.post(
        "/api/categories",
        json={
            "name": "  Salary  ",
            "type": "income",
            "icon": "   ",
            "color": " #00ff00 ",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()["category"]
    assert payload["name"] == "Salary"
    assert payload["type"] == "income"
    assert payload["icon"] is None
    assert payload["color"] == "#00ff00"

    db.expire_all()
    saved = db.query(CategoryModel).filter_by(category_id=payload["category_id"]).one()
    assert saved.user_id == user.user_id


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (None, "Missing request body"),
        ({"name": "", "type": "expense"}, "Category name is required"),
        ({"name": "Food", "type": "wat"}, "Type must be 'income', 'expense', or 'both'"),
    ],
)
def test_create_category_validates_input(authenticated_client, payload, message):
    response = authenticated_client.post("/api/categories", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == message


def test_update_category(authenticated_client, user, category_factory, db):
    category = category_factory(user)

    response = authenticated_client.put(
        f"/api/categories/{category.category_id}",
        json={
            "name": "Groceries",
            "type": "both",
            "icon": "basket",
            "color": "#abcdef",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["category"]["name"] == "Groceries"

    db.expire_all()
    saved = db.get(CategoryModel, category.category_id)
    assert saved.type == "both"
    assert saved.icon == "basket"


def test_delete_category(authenticated_client, user, category_factory, db):
    category = category_factory(user)
    category_id = category.category_id

    response = authenticated_client.delete(f"/api/categories/{category_id}")

    assert response.status_code == 200
    db.expire_all()
    assert db.get(CategoryModel, category_id) is None
