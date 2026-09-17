from src.services.transaction_service import (
    create_transaction,
    delete_transaction,
    get_transaction_for_user,
    get_transactions_for_user,
    update_transaction,
)


def test_create_transaction_with_owned_category(
    db, user_factory, category_factory, sample_datetime, money
):
    user = user_factory()
    category = category_factory(user)

    transaction = create_transaction(
        db,
        user.user_id,
        category.category_id,
        "expense",
        money("19.95"),
        sample_datetime,
        "Lunch",
        "With coworkers",
    )

    assert transaction is not None
    assert transaction.user_id == user.user_id
    assert transaction.category_id == category.category_id
    assert transaction.amount == money("19.95")


def test_create_transaction_rejects_other_users_category(
    db, user_factory, category_factory, sample_datetime, money
):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")
    bobs_category = category_factory(bob)

    transaction = create_transaction(
        db,
        alice.user_id,
        bobs_category.category_id,
        "expense",
        money(20),
        sample_datetime,
        "Should fail",
    )

    assert transaction is None
    assert get_transactions_for_user(db, alice.user_id) == []


def test_get_transaction_is_scoped_to_user(
    db, user_factory, category_factory, sample_datetime, money
):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")
    category = category_factory(alice)
    transaction = create_transaction(
        db, alice.user_id, category.category_id, "expense", money(10),
        sample_datetime, "Coffee"
    )

    assert get_transaction_for_user(db, alice.user_id, transaction.transaction_id) is not None
    assert get_transaction_for_user(db, bob.user_id, transaction.transaction_id) is None


def test_update_transaction_rejects_other_users_category(
    db, user_factory, category_factory, sample_datetime, money
):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")
    alice_category = category_factory(alice, "Food")
    bob_category = category_factory(bob, "Travel")
    transaction = create_transaction(
        db, alice.user_id, alice_category.category_id, "expense", money(10),
        sample_datetime, "Original"
    )

    result = update_transaction(
        db,
        alice.user_id,
        transaction,
        bob_category.category_id,
        "expense",
        money(99),
        sample_datetime,
        "Changed",
    )

    assert result is None
    db.refresh(transaction)
    assert transaction.category_id == alice_category.category_id
    assert transaction.description == "Original"


def test_delete_transaction(db, user_factory, category_factory, sample_datetime, money):
    user = user_factory()
    category = category_factory(user)
    transaction = create_transaction(
        db, user.user_id, category.category_id, "expense", money(10),
        sample_datetime, "Coffee"
    )
    transaction_id = transaction.transaction_id

    delete_transaction(db, transaction)

    assert get_transaction_for_user(db, user.user_id, transaction_id) is None
