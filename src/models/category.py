from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.database import Base


class CategoryModel(Base):
    """
    Represents a user-owned category used to organize transactions and budgets.
    """

    __tablename__ = "category"

    # Columns
    category_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    type = Column(String(20), nullable=False)

    # Foreign key
    user_id = Column(
        Integer,
        ForeignKey("user.user_id"),
        nullable=False
    )
    
    # Relationships
    user = relationship(
        "UserModel",
        back_populates="categories"
    )

    transactions = relationship(
        "TransactionModel",
        back_populates="category"
    )

    budgets = relationship(
        "BudgetModel",
        back_populates="category"
    )