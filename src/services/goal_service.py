from sqlalchemy.orm import Session

from src.models import SavingsGoalModel


def get_goals_for_user(
    db: Session,
    user_id: int
) -> list[SavingsGoalModel]:
    """
    Returns all savings goals owned by a user.
    """

    return (
        db.query(SavingsGoalModel)
        .filter(SavingsGoalModel.user_id == user_id)
        .order_by(SavingsGoalModel.savings_goal_id.desc())
        .all()
    )


def get_shared_goals(
    db: Session
) -> list[SavingsGoalModel]:
    """
    Returns all shared savings goals.
    """

    return (
        db.query(SavingsGoalModel)
        .filter(SavingsGoalModel.scope == "shared")
        .order_by(SavingsGoalModel.savings_goal_id.desc())
        .all()
    )


def get_goal_by_id(
    db: Session,
    goal_id: int
) -> SavingsGoalModel | None:
    """
    Returns a savings goal by ID.
    """

    return (
        db.query(SavingsGoalModel)
        .filter(SavingsGoalModel.savings_goal_id == goal_id)
        .first()
    )


def get_goal_for_user(
    db: Session,
    user_id: int,
    goal_id: int
) -> SavingsGoalModel | None:
    """
    Returns a goal only if the user is allowed to access it.

    Personal goals are accessible only by their owner.
    Shared goals are accessible by every authenticated user.
    """

    goal = get_goal_by_id(
        db=db,
        goal_id=goal_id
    )

    if goal is None:
        return None

    if goal.scope == "shared":
        return goal

    if goal.user_id == user_id:
        return goal

    return None


def create_goal(
    db: Session,
    user_id: int,
    name: str,
    target_amount,
    icon: str | None,
    color: str | None,
    scope: str
) -> SavingsGoalModel:
    """
    Creates a personal or shared savings goal.
    """

    goal = SavingsGoalModel(
        user_id=user_id,
        name=name,
        target_amount=target_amount,
        icon=icon,
        color=color,
        scope=scope
    )

    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal


def update_goal(
    db: Session,
    goal: SavingsGoalModel,
    name: str,
    target_amount,
    icon: str | None,
    color: str | None,
    scope: str
) -> SavingsGoalModel:
    """
    Updates an existing savings goal.
    """

    goal.name = name
    goal.target_amount = target_amount
    goal.icon = icon
    goal.color = color
    goal.scope = scope

    db.commit()
    db.refresh(goal)

    return goal


def delete_goal(
    db: Session,
    goal: SavingsGoalModel
) -> None:
    """
    Deletes a savings goal.
    """

    db.delete(goal)
    db.commit()