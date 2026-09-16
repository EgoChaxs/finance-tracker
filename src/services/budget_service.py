from sqlalchemy.orm import Session

from src.models import BudgetModel
from src.services.category_service import get_category_for_user


def get_budgets_for_user(
    db: Session,
    user_id: int
) -> list[BudgetModel]:
    """
    Returns all budgets belonging to a user.
    """

    return (
        db.query(BudgetModel)
        .filter(BudgetModel.user_id == user_id)
        .order_by(BudgetModel.month.desc())
        .all()
    )


def get_budget_for_user(
    db: Session,
    user_id: int,
    budget_id: int
) -> BudgetModel | None:
    """
    Returns a specific budget only if it belongs
    to the given user.
    """

    return (
        db.query(BudgetModel)
        .filter(
            BudgetModel.budget_id == budget_id,
            BudgetModel.user_id == user_id
        )
        .first()
    )


def create_budget(
    db: Session,
    user_id: int,
    category_id: int,
    amount,
    month
) -> BudgetModel | None:
    """
    Creates a monthly budget for a user.

    Returns None if the selected category does not
    belong to the user.
    """

    category = get_category_for_user(
        db=db,
        user_id=user_id,
        category_id=category_id
    )

    if category is None:
        return None

    budget = BudgetModel(
        user_id=user_id,
        category_id=category_id,
        amount=amount,
        month=month
    )

    db.add(budget)
    db.commit()
    db.refresh(budget)

    return budget


def update_budget(
    db: Session,
    user_id: int,
    budget: BudgetModel,
    category_id: int,
    amount,
    month
) -> BudgetModel | None:
    """
    Updates an existing budget.

    Returns None if the selected category does not
    belong to the user.
    """

    category = get_category_for_user(
        db=db,
        user_id=user_id,
        category_id=category_id
    )

    if category is None:
        return None

    budget.category_id = category_id
    budget.amount = amount
    budget.month = month

    db.commit()
    db.refresh(budget)

    return budget


def delete_budget(
    db: Session,
    budget: BudgetModel
) -> None:
    """
    Deletes an existing budget.
    """

    db.delete(budget)
    db.commit()