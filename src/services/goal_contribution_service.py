from sqlalchemy.orm import Session

from src.models import GoalContributionModel
from src.services.goal_service import get_goal_for_user


def get_contributions_for_goal(
    db: Session,
    user_id: int,
    goal_id: int
) -> list[GoalContributionModel] | None:
    """
    Returns all contributions for a goal if the authenticated
    user is allowed to access that goal.

    Returns None if the goal does not exist or is inaccessible.
    """

    goal = get_goal_for_user(
        db=db,
        user_id=user_id,
        goal_id=goal_id
    )

    if goal is None:
        return None

    return (
        db.query(GoalContributionModel)
        .filter(GoalContributionModel.goal_id == goal_id)
        .order_by(GoalContributionModel.occurred_at.desc())
        .all()
    )


def get_contribution_for_user(
    db: Session,
    user_id: int,
    goal_id: int,
    contribution_id: int
) -> GoalContributionModel | None:
    """
    Returns a contribution only if:
    - it belongs to the specified goal
    - the authenticated user created the contribution
    """

    return (
        db.query(GoalContributionModel)
        .filter(
            GoalContributionModel.contribution_id == contribution_id,
            GoalContributionModel.goal_id == goal_id,
            GoalContributionModel.user_id == user_id
        )
        .first()
    )


def create_contribution(
    db: Session,
    user_id: int,
    goal_id: int,
    amount,
    occurred_at
) -> GoalContributionModel | None:
    """
    Adds a contribution to a goal.

    Returns None if the user cannot access the goal.
    """

    goal = get_goal_for_user(
        db=db,
        user_id=user_id,
        goal_id=goal_id
    )

    if goal is None:
        return None

    contribution = GoalContributionModel(
        goal_id=goal_id,
        user_id=user_id,
        amount=amount,
        occurred_at=occurred_at
    )

    db.add(contribution)
    db.commit()
    db.refresh(contribution)

    return contribution


def delete_contribution(
    db: Session,
    contribution: GoalContributionModel
) -> None:
    """
    Deletes an existing goal contribution.
    """

    db.delete(contribution)
    db.commit()