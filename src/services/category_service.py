from sqlalchemy.orm import Session

from src.models import CategoryModel


def get_categories_for_user(
    db: Session,
    user_id: int
) -> list[CategoryModel]:
    """
    Returns all categories belonging to a user.
    """

    return (
        db.query(CategoryModel)
        .filter(CategoryModel.user_id == user_id)
        .order_by(CategoryModel.name.asc())
        .all()
    )


def get_category_for_user(
    db: Session,
    user_id: int,
    category_id: int
) -> CategoryModel | None:
    """
    Returns a specific category only if it belongs
    to the given user.
    """

    return (
        db.query(CategoryModel)
        .filter(
            CategoryModel.category_id == category_id,
            CategoryModel.user_id == user_id
        )
        .first()
    )


def create_category(
    db: Session,
    user_id: int,
    name: str,
    icon: str | None,
    color: str | None,
    category_type: str
) -> CategoryModel:
    """
    Creates a category belonging to a user.
    """

    category = CategoryModel(
        user_id=user_id,
        name=name,
        icon=icon,
        color=color,
        type=category_type
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


def update_category(
    db: Session,
    category: CategoryModel,
    name: str,
    icon: str | None,
    color: str | None,
    category_type: str
) -> CategoryModel:
    """
    Updates an existing category.
    """

    category.name = name
    category.icon = icon
    category.color = color
    category.type = category_type

    db.commit()
    db.refresh(category)

    return category


def delete_category(
    db: Session,
    category: CategoryModel
) -> None:
    """
    Deletes an existing category.
    """

    db.delete(category)
    db.commit()