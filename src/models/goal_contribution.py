from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from src.database import Base


class GoalContributionModel(Base):
    """
    Represents a user's contribution toward a savings goal.
    """

    __tablename__ = "goal_contribution"

    # Columns
    contribution_id = Column(Integer, primary_key=True)
    amount = Column(Numeric(12, 2), nullable=False)
    occurred_at = Column(DateTime, nullable=False)

    # Foreign keys
    goal_id = Column(
        Integer,
        ForeignKey("savings_goal.savings_goal_id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("user.user_id"),
        nullable=False
    )

    # Relationships
    goal = relationship(
        "SavingsGoalModel",
        back_populates="contributions"
    )

    user = relationship(
        "UserModel",
        back_populates="goal_contributions"
    )