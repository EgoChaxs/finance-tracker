from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, g, jsonify, request

from src.decorators import login_required
from src.database import SessionLocal
from src.services.budget_service import (
    get_budgets_for_user,
    get_budget_for_user,
    create_budget,
    update_budget,
    delete_budget,
)


budgets_bp = Blueprint(
    "budgets",
    __name__,
    url_prefix="/api/budgets"
)


def serialize_budget(budget):
    category = budget.category

    return {
        "budget_id": budget.budget_id,
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
        "amount": float(budget.amount),
        "month": budget.month.isoformat(),
    }


def parse_budget_data(data):
    if not data:
        return None, "Missing request body"

    category_id = data.get("category_id")

    if category_id is None:
        return None, "Category is required"

    try:
        amount = Decimal(str(data.get("amount")))
    except (InvalidOperation, TypeError):
        return None, "Invalid amount"

    if amount <= 0:
        return None, "Amount must be greater than 0"

    try:
        month = datetime.fromisoformat(
            data.get("month")
        )
    except (TypeError, ValueError):
        return None, "Invalid month"

    return {
        "category_id": category_id,
        "amount": amount,
        "month": month,
    }, None


# ==================== GET ALL ====================

@budgets_bp.get("")
@login_required
def get_budgets():
    db = SessionLocal()

    try:
        budgets = get_budgets_for_user(
            db=db,
            user_id=g.current_user.user_id
        )

        return jsonify({
            "budgets": [
                serialize_budget(budget)
                for budget in budgets
            ]
        }), 200

    finally:
        db.close()


# ==================== GET ONE ====================

@budgets_bp.get("/<int:budget_id>")
@login_required
def get_budget(budget_id):
    db = SessionLocal()

    try:
        budget = get_budget_for_user(
            db=db,
            user_id=g.current_user.user_id,
            budget_id=budget_id
        )

        if budget is None:
            return jsonify({
                "message": "Budget not found"
            }), 404

        return jsonify(
            serialize_budget(budget)
        ), 200

    finally:
        db.close()


# ==================== CREATE ====================

@budgets_bp.post("")
@login_required
def create():
    data = request.get_json(silent=True)

    parsed, error = parse_budget_data(data)

    if error:
        return jsonify({
            "message": error
        }), 400

    db = SessionLocal()

    try:
        budget = create_budget(
            db=db,
            user_id=g.current_user.user_id,
            **parsed
        )

        if budget is None:
            return jsonify({
                "message": "Category not found"
            }), 404

        return jsonify({
            "message": "Budget created",
            "budget": serialize_budget(budget)
        }), 201

    finally:
        db.close()


# ==================== UPDATE ====================

@budgets_bp.put("/<int:budget_id>")
@login_required
def update(budget_id):
    data = request.get_json(silent=True)

    parsed, error = parse_budget_data(data)

    if error:
        return jsonify({
            "message": error
        }), 400

    db = SessionLocal()

    try:
        budget = get_budget_for_user(
            db=db,
            user_id=g.current_user.user_id,
            budget_id=budget_id
        )

        if budget is None:
            return jsonify({
                "message": "Budget not found"
            }), 404

        budget = update_budget(
            db=db,
            user_id=g.current_user.user_id,
            budget=budget,
            **parsed
        )

        if budget is None:
            return jsonify({
                "message": "Category not found"
            }), 404

        return jsonify({
            "message": "Budget updated",
            "budget": serialize_budget(budget)
        }), 200

    finally:
        db.close()


# ==================== DELETE ====================

@budgets_bp.delete("/<int:budget_id>")
@login_required
def delete(budget_id):
    db = SessionLocal()

    try:
        budget = get_budget_for_user(
            db=db,
            user_id=g.current_user.user_id,
            budget_id=budget_id
        )

        if budget is None:
            return jsonify({
                "message": "Budget not found"
            }), 404

        delete_budget(
            db=db,
            budget=budget
        )

        return jsonify({
            "message": "Budget deleted"
        }), 200

    finally:
        db.close()