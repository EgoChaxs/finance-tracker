from flask import Blueprint, g, jsonify, request

from src.decorators import login_required
from src.database import SessionLocal
from src.services.category_service import (
    get_categories_for_user,
    get_category_for_user,
    create_category,
    update_category,
    delete_category,
)


categories_bp = Blueprint(
    "categories",
    __name__,
    url_prefix="/api/categories"
)


def serialize_category(category):
    return {
        "category_id": category.category_id,
        "name": category.name,
        "icon": category.icon,
        "color": category.color,
        "type": category.type,
    }


def parse_category_data(data):
    if not data:
        return None, "Missing request body"

    name = data.get("name", "").strip()
    icon = data.get("icon")
    color = data.get("color")
    category_type = data.get("type")

    if not name:
        return None, "Category name is required"

    if category_type not in ("income", "expense", "both"):
        return None, "Type must be 'income', 'expense', or 'both'"

    if icon is not None:
        icon = str(icon).strip() or None

    if color is not None:
        color = str(color).strip() or None

    return {
        "name": name,
        "icon": icon,
        "color": color,
        "category_type": category_type,
    }, None


@categories_bp.get("")
@login_required
def get_categories():
    db = SessionLocal()

    try:
        categories = get_categories_for_user(
            db=db,
            user_id=g.current_user.user_id
        )

        return jsonify({
            "categories": [
                serialize_category(category)
                for category in categories
            ]
        }), 200

    finally:
        db.close()


@categories_bp.get("/<int:category_id>")
@login_required
def get_category(category_id):
    db = SessionLocal()

    try:
        category = get_category_for_user(
            db=db,
            user_id=g.current_user.user_id,
            category_id=category_id
        )

        if category is None:
            return jsonify({
                "message": "Category not found"
            }), 404

        return jsonify(
            serialize_category(category)
        ), 200

    finally:
        db.close()


@categories_bp.post("")
@login_required
def create():
    data = request.get_json(silent=True)

    parsed, error = parse_category_data(data)

    if error:
        return jsonify({
            "message": error
        }), 400

    db = SessionLocal()

    try:
        category = create_category(
            db=db,
            user_id=g.current_user.user_id,
            **parsed
        )

        return jsonify({
            "message": "Category created",
            "category": serialize_category(category)
        }), 201

    finally:
        db.close()


@categories_bp.put("/<int:category_id>")
@login_required
def update(category_id):
    data = request.get_json(silent=True)

    parsed, error = parse_category_data(data)

    if error:
        return jsonify({
            "message": error
        }), 400

    db = SessionLocal()

    try:
        category = get_category_for_user(
            db=db,
            user_id=g.current_user.user_id,
            category_id=category_id
        )

        if category is None:
            return jsonify({
                "message": "Category not found"
            }), 404

        category = update_category(
            db=db,
            category=category,
            **parsed
        )

        return jsonify({
            "message": "Category updated",
            "category": serialize_category(category)
        }), 200

    finally:
        db.close()


@categories_bp.delete("/<int:category_id>")
@login_required
def delete(category_id):
    db = SessionLocal()

    try:
        category = get_category_for_user(
            db=db,
            user_id=g.current_user.user_id,
            category_id=category_id
        )

        if category is None:
            return jsonify({
                "message": "Category not found"
            }), 404

        delete_category(
            db=db,
            category=category
        )

        return jsonify({
            "message": "Category deleted"
        }), 200

    finally:
        db.close()