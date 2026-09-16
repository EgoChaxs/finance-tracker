from sqlalchemy.orm import Session

from src.models import TransactionModel
from src.services.category_service import get_category_for_user


def get_transactions_for_user(
    db: Session,
    user_id: int
) -> list[TransactionModel]:
    return (
        db.query(TransactionModel)
        .filter(TransactionModel.user_id == user_id)
        .order_by(TransactionModel.occurred_at.desc())
        .all()
    )


def get_transaction_for_user(
    db: Session,
    user_id: int,
    transaction_id: int
) -> TransactionModel | None:
    return (
        db.query(TransactionModel)
        .filter(
            TransactionModel.transaction_id == transaction_id,
            TransactionModel.user_id == user_id
        )
        .first()
    )


def create_transaction(
    db: Session,
    user_id: int,
    category_id: int,
    transaction_type: str,
    amount,
    occurred_at,
    description: str,
    notes: str | None = None
) -> TransactionModel | None:

    category = get_category_for_user(
        db=db,
        user_id=user_id,
        category_id=category_id
    )

    if category is None:
        return None

    transaction = TransactionModel(
        user_id=user_id,
        category_id=category_id,
        type=transaction_type,
        amount=amount,
        occurred_at=occurred_at,
        description=description,
        notes=notes
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def update_transaction(
    db: Session,
    user_id: int,
    transaction: TransactionModel,
    category_id: int,
    transaction_type: str,
    amount,
    occurred_at,
    description: str,
    notes: str | None = None
) -> TransactionModel | None:

    category = get_category_for_user(
        db=db,
        user_id=user_id,
        category_id=category_id
    )

    if category is None:
        return None

    transaction.category_id = category_id
    transaction.type = transaction_type
    transaction.amount = amount
    transaction.occurred_at = occurred_at
    transaction.description = description
    transaction.notes = notes

    db.commit()
    db.refresh(transaction)

    return transaction


def delete_transaction(
    db: Session,
    transaction: TransactionModel
) -> None:
    db.delete(transaction)
    db.commit()