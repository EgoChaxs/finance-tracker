from datetime import datetime
from decimal import Decimal

import pytest

from src.models import BudgetModel


def budget_payload(category_id, **overrides):
    payload = {
        "category_id": category_id,
        "amount": "500.00",
        "month": "2026-09-01T00:00:00",
    }
    payload.update(overrides)
    return payload


def add_budget(db, user, category, amount="100.00"):
    budget = BudgetModel(
        user_id=user.user_id,
        category_id=category.category_id,
        amount=Decimal(amount),
        month=datetime(2026, 9, 1),
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def test_create_budget(authenticated_client, user, category_factory, db):
    category = category_factory(user)

    response = authenticated_client.post(
        "/api/budgets",
        json=budget_payload(category.category_id),
    )

    assert response.status_code == 201
    payload = response.get_json()["budget"]
    assert payload["amount"] == 500.0
    assert payload["month"] == "2026-09-01T00:00:00"

    db.expire_all()
    saved = db.get(BudgetModel, payload["budget_id"])
    assert saved.user_id == user.user_id


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (None, "Missing request body"),
        ({}, "Missing request body"),
        ({"amount": 10, "month": "2026-09-01"}, "Category is required"),
        ({"category_id": 1, "amount": "nope"}, "Invalid amount"),
        ({"category_id": 1, "amount": 0}, "Amount must be greater than 0"),
        ({"category_id": 1, "amount": 10, "month": "bad"}, "Invalid month"),
    ],
)
def test_create_budget_validates_input(authenticated_client, payload, message):
    response = authenticated_client.post("/api/budgets", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == message


def test_create_budget_rejects_another_users_category(
    authenticated_client,
    second_user,
    category_factory,
):
    category = category_factory(second_user)

    response = authenticated_client.post(
        "/api/budgets",
        json=budget_payload(category.category_id),
    )

    assert response.status_code == 404
    assert response.get_json()["message"] == "Category not found"


def test_get_budgets_returns_only_current_users_budgets(
    authenticated_client,
    user,
    second_user,
    category_factory,
    db,
):
    own_category = category_factory(user, name="Own")
    other_category = category_factory(second_user, name="Other")
    own = add_budget(db, user, own_category)
    add_budget(db, second_user, other_category)

    response = authenticated_client.get("/api/budgets")

    assert response.status_code == 200
    budgets = response.get_json()["budgets"]
    assert [item["budget_id"] for item in budgets] == [own.budget_id]


def test_get_budget_hides_another_users_budget(
    authenticated_client,
    second_user,
    category_factory,
    db,
):
    category = category_factory(second_user)
    budget = add_budget(db, second_user, category)

    response = authenticated_client.get(f"/api/budgets/{budget.budget_id}")

    assert response.status_code == 404


def test_update_budget(authenticated_client, user, category_factory, db):
    old_category = category_factory(user, name="Old")
    new_category = category_factory(user, name="New")
    budget = add_budget(db, user, old_category)

    response = authenticated_client.put(
        f"/api/budgets/{budget.budget_id}",
        json=budget_payload(
            new_category.category_id,
            amount="750.00",
            month="2026-10-01T00:00:00",
        ),
    )

    assert response.status_code == 200
    assert response.get_json()["budget"]["amount"] == 750.0

    db.expire_all()
    saved = db.get(BudgetModel, budget.budget_id)
    assert saved.category_id == new_category.category_id
    assert saved.month == datetime(2026, 10, 1)


def test_delete_budget(authenticated_client, user, category_factory, db):
    category = category_factory(user)
    budget = add_budget(db, user, category)
    budget_id = budget.budget_id

    response = authenticated_client.delete(f"/api/budgets/{budget_id}")

    assert response.status_code == 200
    db.expire_all()
    assert db.get(BudgetModel, budget_id) is None
