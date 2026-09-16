from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from src.database import Base


class BudgetModel(Base):
    """
    Represents a user's monthly spending budget for a category.
    """

    __tablename__ = "budget"

    # Columns
    budget_id = Column(Integer, primary_key=True)
    amount = Column(Numeric(12, 2), nullable=False)
    month = Column(DateTime, nullable=False)

    # Foreign keys
    user_id = Column(
        Integer,
        ForeignKey("user.user_id"),
        nullable=False
    )

    category_id = Column(
        Integer,
        ForeignKey(
            "category.category_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # Relationships
    user = relationship(
        "UserModel",
        back_populates="budgets"
    )

    category = relationship(
        "CategoryModel",
        back_populates="budgets"
    )