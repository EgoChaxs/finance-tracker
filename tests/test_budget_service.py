from datetime import datetime

from src.services.budget_service import (
    create_budget,
    delete_budget,
    get_budget_for_user,
    get_budgets_for_user,
    update_budget,
)


def test_create_budget_with_owned_category(db, user_factory, category_factory, money):
    user = user_factory()
    category = category_factory(user)
    month = datetime(2026, 9, 1)

    budget = create_budget(db, user.user_id, category.category_id, money(400), month)

    assert budget is not None
    assert budget.amount == money(400)
    assert budget.category_id == category.category_id


def test_create_budget_rejects_other_users_category(
    db, user_factory, category_factory, money
):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")
    bobs_category = category_factory(bob)

    budget = create_budget(
        db, alice.user_id, bobs_category.category_id, money(100), datetime(2026, 9, 1)
    )

    assert budget is None
    assert get_budgets_for_user(db, alice.user_id) == []


def test_get_budget_is_scoped_to_user(db, user_factory, category_factory, money):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")
    category = category_factory(alice)
    budget = create_budget(
        db, alice.user_id, category.category_id, money(100), datetime(2026, 9, 1)
    )

    assert get_budget_for_user(db, alice.user_id, budget.budget_id) is not None
    assert get_budget_for_user(db, bob.user_id, budget.budget_id) is None


def test_update_budget(db, user_factory, category_factory, money):
    user = user_factory()
    food = category_factory(user, "Food")
    travel = category_factory(user, "Travel")
    budget = create_budget(
        db, user.user_id, food.category_id, money(100), datetime(2026, 9, 1)
    )

    updated = update_budget(
        db,
        user.user_id,
        budget,
        travel.category_id,
        money(250),
        datetime(2026, 10, 1),
    )

    assert updated.category_id == travel.category_id
    assert updated.amount == money(250)
    assert updated.month == datetime(2026, 10, 1)


def test_delete_budget(db, user_factory, category_factory, money):
    user = user_factory()
    category = category_factory(user)
    budget = create_budget(
        db, user.user_id, category.category_id, money(100), datetime(2026, 9, 1)
    )
    budget_id = budget.budget_id

    delete_budget(db, budget)

    assert get_budget_for_user(db, user.user_id, budget_id) is None
