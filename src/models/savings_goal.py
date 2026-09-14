from sqlalchemy import Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from src.database import Base


class SavingsGoalModel(Base):
    """
    Represents a personal or shared savings goal.
    """

    __tablename__ = "savings_goal"

    # Columns
    savings_goal_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    target_amount = Column(Numeric(12, 2), nullable=False)
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    scope = Column(String(20), nullable=False)

    # Foreign key
    user_id = Column(
        Integer,
        ForeignKey("user.user_id"),
        nullable=False
    )

    # Relationships
    user = relationship(
        "UserModel",
        back_populates="savings_goals"
    )

    contributions = relationship(
        "GoalContributionModel",
        back_populates="goal"
    )