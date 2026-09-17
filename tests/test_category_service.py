from src.services.category_service import (
    create_category,
    delete_category,
    get_categories_for_user,
    get_category_for_user,
    update_category,
)


def test_create_and_get_category(db, user_factory):
    user = user_factory()

    category = create_category(
        db=db,
        user_id=user.user_id,
        name="Salary",
        icon="fas fa-money-bill",
        color="#00aa88",
        category_type="income",
    )

    found = get_category_for_user(db, user.user_id, category.category_id)

    assert found is not None
    assert found.name == "Salary"
    assert found.type == "income"


def test_categories_are_scoped_to_user(db, user_factory):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")

    create_category(db, alice.user_id, "Food", None, None, "expense")
    create_category(db, bob.user_id, "Salary", None, None, "income")

    alice_categories = get_categories_for_user(db, alice.user_id)

    assert [category.name for category in alice_categories] == ["Food"]


def test_get_category_rejects_other_users_category(db, user_factory, category_factory):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")
    category = category_factory(bob)

    assert get_category_for_user(db, alice.user_id, category.category_id) is None


def test_update_category(db, user_factory, category_factory):
    user = user_factory()
    category = category_factory(user)

    updated = update_category(
        db,
        category,
        "Groceries",
        "fas fa-cart-shopping",
        "#abcdef",
        "expense",
    )

    assert updated.name == "Groceries"
    assert updated.icon == "fas fa-cart-shopping"
    assert updated.color == "#abcdef"


def test_delete_category(db, user_factory, category_factory):
    user = user_factory()
    category = category_factory(user)
    category_id = category.category_id

    delete_category(db, category)

    assert get_category_for_user(db, user.user_id, category_id) is None
