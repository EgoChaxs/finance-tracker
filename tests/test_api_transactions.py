from datetime import datetime
from decimal import Decimal

import pytest

from src.models import TransactionModel


def transaction_payload(category_id, **overrides):
    payload = {
        "category_id": category_id,
        "type": "expense",
        "amount": "42.50",
        "occurred_at": "2026-09-17T18:30:00",
        "description": "Groceries",
        "notes": "Weekly shop",
    }
    payload.update(overrides)
    return payload


def add_transaction(db, user, category, description="Existing", amount="12.00"):
    transaction = TransactionModel(
        user_id=user.user_id,
        category_id=category.category_id,
        type="expense",
        amount=Decimal(amount),
        occurred_at=datetime(2026, 9, 17, 10, 0),
        description=description,
        notes=None,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def test_create_transaction_persists_for_authenticated_user(
    authenticated_client,
    user,
    category_factory,
    db,
):
    category = category_factory(user)

    response = authenticated_client.post(
        "/api/transactions",
        json=transaction_payload(category.category_id),
    )

    assert response.status_code == 201
    payload = response.get_json()["transaction"]
    assert payload["amount"] == 42.5
    assert payload["category"]["category_id"] == category.category_id
    assert payload["occurred_at"] == "2026-09-17T18:30:00"

    db.expire_all()
    saved = db.get(TransactionModel, payload["transaction_id"])
    assert saved.user_id == user.user_id
    assert saved.description == "Groceries"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (None, "Missing request body"),
        ({"type": "transfer"}, "Type must be 'income' or 'expense'"),
        ({"type": "expense", "description": "x"}, "Category is required"),
        ({"type": "expense", "category_id": 1, "description": "   "}, "Description is required"),
        (
            {"type": "expense", "category_id": 1, "description": "x", "amount": "nope"},
            "Invalid amount",
        ),
        (
            {"type": "expense", "category_id": 1, "description": "x", "amount": 0},
            "Amount must be greater than 0",
        ),
        (
            {
                "type": "expense",
                "category_id": 1,
                "description": "x",
                "amount": 1,
                "occurred_at": "not-a-date",
            },
            "Invalid occurred_at datetime",
        ),
    ],
)
def test_create_transaction_validates_input(authenticated_client, payload, message):
    response = authenticated_client.post("/api/transactions", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == message


def test_create_transaction_rejects_another_users_category(
    authenticated_client,
    second_user,
    category_factory,
):
    category = category_factory(second_user)

    response = authenticated_client.post(
        "/api/transactions",
        json=transaction_payload(category.category_id),
    )

    assert response.status_code == 404
    assert response.get_json()["message"] == "Category not found"


def test_get_transactions_hides_other_users_transactions(
    authenticated_client,
    user,
    second_user,
    category_factory,
    db,
):
    own_category = category_factory(user, name="Own")
    other_category = category_factory(second_user, name="Other")
    own = add_transaction(db, user, own_category, description="Mine")
    add_transaction(db, second_user, other_category, description="Not mine")

    response = authenticated_client.get("/api/transactions")

    assert response.status_code == 200
    transactions = response.get_json()["transactions"]
    assert [item["transaction_id"] for item in transactions] == [own.transaction_id]


def test_get_transaction_hides_another_users_transaction(
    authenticated_client,
    second_user,
    category_factory,
    db,
):
    category = category_factory(second_user)
    transaction = add_transaction(db, second_user, category)

    response = authenticated_client.get(
        f"/api/transactions/{transaction.transaction_id}"
    )

    assert response.status_code == 404


def test_update_transaction(authenticated_client, user, category_factory, db):
    old_category = category_factory(user, name="Old")
    new_category = category_factory(user, name="New")
    transaction = add_transaction(db, user, old_category)

    response = authenticated_client.put(
        f"/api/transactions/{transaction.transaction_id}",
        json=transaction_payload(
            new_category.category_id,
            type="income",
            amount="99.99",
            description="Refund",
            notes="   ",
        ),
    )

    assert response.status_code == 200
    payload = response.get_json()["transaction"]
    assert payload["type"] == "income"
    assert payload["amount"] == 99.99
    assert payload["notes"] is None

    db.expire_all()
    saved = db.get(TransactionModel, transaction.transaction_id)
    assert saved.category_id == new_category.category_id
    assert saved.description == "Refund"


def test_deleted_category_serializes_as_unknown(
    authenticated_client,
    user,
    category_factory,
    db,
):
    category = category_factory(user)
    transaction = add_transaction(db, user, category)
    category_id = category.category_id

    delete_response = authenticated_client.delete(f"/api/categories/{category_id}")
    assert delete_response.status_code == 200

    response = authenticated_client.get(
        f"/api/transactions/{transaction.transaction_id}"
    )

    assert response.status_code == 200
    assert response.get_json()["category"] == {
        "category_id": None,
        "name": "Unknown",
        "icon": None,
        "color": None,
    }


def test_delete_transaction(authenticated_client, user, category_factory, db):
    category = category_factory(user)
    transaction = add_transaction(db, user, category)
    transaction_id = transaction.transaction_id

    response = authenticated_client.delete(f"/api/transactions/{transaction_id}")

    assert response.status_code == 200
    db.expire_all()
    assert db.get(TransactionModel, transaction_id) is None
