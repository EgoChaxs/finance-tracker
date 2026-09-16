from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, g, jsonify, request

from src.decorators import login_required
from src.database import SessionLocal
from src.services.goal_service import (
    get_goals_for_user,
    get_shared_goals,
    get_goal_for_user,
    create_goal,
    update_goal,
    delete_goal,
)
from src.services.goal_contribution_service import (
    get_contributions_for_goal,
    get_contribution_for_user,
    create_contribution,
    delete_contribution,
)


goals_bp = Blueprint(
    "goals",
    __name__,
    url_prefix="/api/goals"
)


def serialize_contribution(contribution):
    return {
        "contribution_id": contribution.contribution_id,
        "user_id": contribution.user_id,
        "amount": float(contribution.amount),
        "occurred_at": contribution.occurred_at.isoformat(),
    }


def serialize_goal(goal):
    return {
        "goal_id": goal.savings_goal_id,
        "owner_user_id": goal.user_id,
        "name": goal.name,
        "target_amount": float(goal.target_amount),
        "icon": goal.icon,
        "color": goal.color,
        "scope": goal.scope,
    }


def parse_goal_data(data):
    if not data:
        return None, "Missing request body"

    name = data.get("name", "").strip()
    icon = data.get("icon")
    color = data.get("color")
    scope = data.get("scope")

    if not name:
        return None, "Goal name is required"

    if scope not in ("personal", "shared"):
        return None, "Scope must be 'personal' or 'shared'"

    try:
        target_amount = Decimal(str(data.get("target_amount")))
    except (InvalidOperation, TypeError):
        return None, "Invalid target amount"

    if target_amount <= 0:
        return None, "Target amount must be greater than 0"

    if icon is not None:
        icon = str(icon).strip() or None

    if color is not None:
        color = str(color).strip() or None

    return {
        "name": name,
        "target_amount": target_amount,
        "icon": icon,
        "color": color,
        "scope": scope,
    }, None


def parse_contribution_data(data):
    if not data:
        return None, "Missing request body"

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

    return {
        "amount": amount,
        "occurred_at": occurred_at,
    }, None


# ==================== GET GOALS ====================

@goals_bp.get("")
@login_required
def get_goals():
    db = SessionLocal()

    try:
        personal_goals = get_goals_for_user(
            db=db,
            user_id=g.current_user.user_id
        )

        shared_goals = get_shared_goals(db)

        goals = {
            goal.savings_goal_id: goal
            for goal in [*personal_goals, *shared_goals]
        }

        return jsonify({
            "goals": [
                serialize_goal(goal)
                for goal in goals.values()
            ]
        }), 200

    finally:
        db.close()


# ==================== GET ONE GOAL ====================

@goals_bp.get("/<int:goal_id>")
@login_required
def get_goal(goal_id):
    db = SessionLocal()

    try:
        goal = get_goal_for_user(
            db=db,
            user_id=g.current_user.user_id,
            goal_id=goal_id
        )

        if goal is None:
            return jsonify({
                "message": "Goal not found"
            }), 404

        return jsonify(
            serialize_goal(goal)
        ), 200

    finally:
        db.close()


# ==================== CREATE GOAL ====================

@goals_bp.post("")
@login_required
def create():
    data = request.get_json(silent=True)

    parsed, error = parse_goal_data(data)

    if error:
        return jsonify({
            "message": error
        }), 400

    db = SessionLocal()

    try:
        goal = create_goal(
            db=db,
            user_id=g.current_user.user_id,
            **parsed
        )

        return jsonify({
            "message": "Goal created",
            "goal": serialize_goal(goal)
        }), 201

    finally:
        db.close()


# ==================== UPDATE GOAL ====================

@goals_bp.put("/<int:goal_id>")
@login_required
def update(goal_id):
    data = request.get_json(silent=True)

    parsed, error = parse_goal_data(data)

    if error:
        return jsonify({
            "message": error
        }), 400

    db = SessionLocal()

    try:
        goal = get_goal_for_user(
            db=db,
            user_id=g.current_user.user_id,
            goal_id=goal_id
        )

        if goal is None:
            return jsonify({
                "message": "Goal not found"
            }), 404

        if goal.user_id != g.current_user.user_id:
            return jsonify({
                "message": "Only the goal owner can update this goal"
            }), 403

        goal = update_goal(
            db=db,
            goal=goal,
            **parsed
        )

        return jsonify({
            "message": "Goal updated",
            "goal": serialize_goal(goal)
        }), 200

    finally:
        db.close()


# ==================== DELETE GOAL ====================

@goals_bp.delete("/<int:goal_id>")
@login_required
def delete(goal_id):
    db = SessionLocal()

    try:
        goal = get_goal_for_user(
            db=db,
            user_id=g.current_user.user_id,
            goal_id=goal_id
        )

        if goal is None:
            return jsonify({
                "message": "Goal not found"
            }), 404

        if goal.user_id != g.current_user.user_id:
            return jsonify({
                "message": "Only the goal owner can delete this goal"
            }), 403

        delete_goal(
            db=db,
            goal=goal
        )

        return jsonify({
            "message": "Goal deleted"
        }), 200

    finally:
        db.close()


# ==================== GET CONTRIBUTIONS ====================

@goals_bp.get("/<int:goal_id>/contributions")
@login_required
def get_contributions(goal_id):
    db = SessionLocal()

    try:
        contributions = get_contributions_for_goal(
            db=db,
            user_id=g.current_user.user_id,
            goal_id=goal_id
        )

        if contributions is None:
            return jsonify({
                "message": "Goal not found"
            }), 404

        return jsonify({
            "contributions": [
                serialize_contribution(contribution)
                for contribution in contributions
            ]
        }), 200

    finally:
        db.close()


# ==================== ADD CONTRIBUTION ====================

@goals_bp.post("/<int:goal_id>/contributions")
@login_required
def add_contribution(goal_id):
    data = request.get_json(silent=True)

    parsed, error = parse_contribution_data(data)

    if error:
        return jsonify({
            "message": error
        }), 400

    db = SessionLocal()

    try:
        contribution = create_contribution(
            db=db,
            user_id=g.current_user.user_id,
            goal_id=goal_id,
            **parsed
        )

        if contribution is None:
            return jsonify({
                "message": "Goal not found"
            }), 404

        return jsonify({
            "message": "Contribution added",
            "contribution": serialize_contribution(contribution)
        }), 201

    finally:
        db.close()


# ==================== DELETE CONTRIBUTION ====================

@goals_bp.delete(
    "/<int:goal_id>/contributions/<int:contribution_id>"
)
@login_required
def remove_contribution(goal_id, contribution_id):
    db = SessionLocal()

    try:
        contribution = get_contribution_for_user(
            db=db,
            user_id=g.current_user.user_id,
            goal_id=goal_id,
            contribution_id=contribution_id
        )

        if contribution is None:
            return jsonify({
                "message": "Contribution not found"
            }), 404

        delete_contribution(
            db=db,
            contribution=contribution
        )

        return jsonify({
            "message": "Contribution deleted"
        }), 200

    finally:
        db.close()