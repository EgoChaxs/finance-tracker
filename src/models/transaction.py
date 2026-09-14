from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from src.database import Base


class TransactionModel(Base):
    """
    Represents an income or expense transaction made by a user.
    """

    __tablename__ = "transaction"

    # Columns
    transaction_id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)

    #Foreign keys
    user_id = Column(
        Integer,
        ForeignKey("user.user_id"),
        nullable=False
    )

    category_id = Column(
        Integer,
        ForeignKey("category.category_id"),
        nullable=True
    )

    # Relationships
    user = relationship(
        "UserModel",
        back_populates="transactions"
    )

    category = relationship(
        "CategoryModel",
        back_populates="transactions"
    )