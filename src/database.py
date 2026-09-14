from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine(
    "sqlite:///data/finance_tracker.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

from src.models import (
    UserModel,
    TransactionModel,
    SessionModel,
    SavingsGoalModel,
    GoalContributionModel,
    CategoryModel,
    BudgetModel
)