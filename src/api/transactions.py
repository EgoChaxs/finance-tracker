from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, g, jsonify, request

from src.decorators import login_required
from src.database import SessionLocal
from src.services.transaction_service import (
    get_transactions_for_user,
    get_transaction_for_user,
    create_transaction,
    update_transaction,
    delete_transaction,
)


transactions_bp = Blueprint(
    "transactions",
    __name__,
    url_prefix="/api/transactions"
)


def serialize_transaction(transaction):
    """
    Converts a TransactionModel into JSON-friendly data.
    """

    category = transaction.category

    return {
        "transaction_id": transaction.transaction_id,

        "category": {
            "category_id": category.category_id,
            "name": category.name,
            "icon": category.icon,
            "color": category.color,
        } if category is not None else {
            "category_id": None,
            "name": "Unknown",
            "icon": None,
            "color": None,
        },

        "type": transaction.type,
        "amount": float(transaction.amount),
        "occurred_at": transaction.occurred_at.isoformat(),
        "description": transaction.description,
        "notes": transaction.notes,
    }


def parse_transaction_data(data):
    """
    Validates and parses transaction request data.

    Returns:
        (parsed_data, None) on success
        (None, error_message) on failure
    """

    if not data:
        return None, "Missing request body"

    transaction_type = data.get("type")
    category_id = data.get("category_id")
    description = data.get("description", "").strip()
    notes = data.get("notes")

    if transaction_type not in ("income", "expense"):
        return None, "Type must be 'income' or 'expense'"

    if category_id is None:
        return None, "Category is required"

    if not description:
        return None, "Description is required"

    try:
        amount = Decimal(str(data.get("amount")))
    except (InvalidOperation, TypeError):
        return None, "Invalid amount"

    if amount <= 0:
        return None, "Amount must be greater than 0"

    try:
        occurred_at = datetime.fromisoformat(
            data.get("occurred_at")
        )
    except (TypeError, ValueError):
        return None, "Invalid occurred_at datetime"

    if notes is not None:
        notes = str(notes).strip() or None

    return {
        "category_id": category_id,
        "transaction_type": transaction_type,
        "amount": amount,
        "occurred_at": occurred_at,
        "description": description,
        "notes": notes,
    }, None


# ==================== GET ALL ====================

@transactions_bp.get("")
@login_required
def get_transactions():
    """
    Returns all transactions belonging to
    the authenticated user.
    """

    db = SessionLocal()

    try:
        transactions = get_transactions_for_user(
            db=db,
            user_id=g.current_user.user_id
        )

        return jsonify({
            "transactions": [
                serialize_transaction(transaction)
                for transaction in transactions
            ]
        }), 200

    finally:
        db.close()


# ==================== GET ONE ====================

@transactions_bp.get("/<int:transaction_id>")
@login_required
def get_transaction(transaction_id):
    """
    Returns one transaction belonging to
    the authenticated user.
    """

    db = SessionLocal()

    try:
        transaction = get_transaction_for_user(
            db=db,
            user_id=g.current_user.user_id,
            transaction_id=transaction_id
        )

        if transaction is None:
            return jsonify({
                "message": "Transaction not found"
            }), 404

        return jsonify(
            serialize_transaction(transaction)
        ), 200

    finally:
        db.close()


# ==================== CREATE ====================

@transactions_bp.post("")
@login_required
def create():
    """
    Creates a transaction for the authenticated user.
    """

    data = request.get_json(silent=True)

    parsed, error = parse_transaction_data(data)

    if error:
        return jsonify({
            "message": error
        }), 400

    db = SessionLocal()

    try:
        transaction = create_transaction(
            db=db,
            user_id=g.current_user.user_id,
            **parsed
        )

        if transaction is None:
            return jsonify({
                "message": "Category not found"
            }), 404

        return jsonify({
            "message": "Transaction created",
            "transaction": serialize_transaction(transaction)
        }), 201

    finally:
        db.close()


# ==================== UPDATE ====================

@transactions_bp.put("/<int:transaction_id>")
@login_required
def update(transaction_id):
    """
    Updates one of the authenticated user's transactions.
    """

    data = request.get_json(silent=True)

    parsed, error = parse_transaction_data(data)

    if error:
        return jsonify({
            "message": error
        }), 400

    db = SessionLocal()

    try:
        transaction = get_transaction_for_user(
            db=db,
            user_id=g.current_user.user_id,
            transaction_id=transaction_id
        )

        if transaction is None:
            return jsonify({
                "message": "Transaction not found"
            }), 404

        transaction = update_transaction(
            db=db,
            user_id=g.current_user.user_id,
            transaction=transaction,
            **parsed
        )

        if transaction is None:
            return jsonify({
                "message": "Category not found"
            }), 404

        return jsonify({
            "message": "Transaction updated",
            "transaction": serialize_transaction(transaction)
        }), 200

    finally:
        db.close()


# ==================== DELETE ====================

@transactions_bp.delete("/<int:transaction_id>")
@login_required
def delete(transaction_id):
    """
    Deletes one of the authenticated user's transactions.
    """

    db = SessionLocal()

    try:
        transaction = get_transaction_for_user(
            db=db,
            user_id=g.current_user.user_id,
            transaction_id=transaction_id
        )

        if transaction is None:
            return jsonify({
                "message": "Transaction not found"
            }), 404

        delete_transaction(
            db=db,
            transaction=transaction
        )

        return jsonify({
            "message": "Transaction deleted"
        }), 200

    finally:
        db.close()