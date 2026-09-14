from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.database import Base


class SessionModel(Base):
    """
    Represents an authenticated browser session belonging to a user.
    """

    __tablename__ = "session"

    # Columns
    session_id = Column(Integer, primary_key=True)
    session_identifier = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Foreign key
    user_id = Column(
        Integer,
        ForeignKey("user.user_id"),
        nullable=False
    )
    
    # Relationships
    user = relationship(
        "UserModel",
        back_populates="sessions"
    )