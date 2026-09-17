from datetime import datetime

from src.models import BudgetModel, TransactionModel
from src.services.budget_service import create_budget
from src.services.category_service import delete_category
from src.services.transaction_service import create_transaction


def test_deleting_category_preserves_transaction_as_unknown_and_deletes_budget(
    db, user_factory, category_factory, sample_datetime, money
):
    user = user_factory()
    category = category_factory(user, "Groceries")

    transaction = create_transaction(
        db,
        user.user_id,
        category.category_id,
        "expense",
        money(30),
        sample_datetime,
        "Groceries",
    )
    budget = create_budget(
        db,
        user.user_id,
        category.category_id,
        money(300),
        datetime(2026, 9, 1),
    )

    transaction_id = transaction.transaction_id
    budget_id = budget.budget_id

    delete_category(db, category)

    preserved_transaction = db.get(TransactionModel, transaction_id)
    deleted_budget = db.get(BudgetModel, budget_id)

    assert preserved_transaction is not None
    assert preserved_transaction.category_id is None
    assert deleted_budget is None
