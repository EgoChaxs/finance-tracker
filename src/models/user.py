from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from src.database import Base


class UserModel(Base):
    """
    Represents a family member who can access the finance tracker.
    """

    __tablename__ = "user"

    # Columns
    user_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    hashed_access_key = Column(String(255), nullable=False, unique=True)

    # Relationships
    transactions = relationship(
        "TransactionModel",
        back_populates="user"
    )

    sessions = relationship(
        "SessionModel",
        back_populates="user"
    )

    categories = relationship(
        "CategoryModel",
        back_populates="user"
    )

    budgets = relationship(
        "BudgetModel",
        back_populates="user"
    )

    savings_goals = relationship(
        "SavingsGoalModel",
        back_populates="user"
    )

    goal_contributions = relationship(
        "GoalContributionModel",
        back_populates="user"
    )