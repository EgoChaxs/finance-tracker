from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine(
    "sqlite:///data/finance_tracker.db",
    connect_args={"check_same_thread": False}
)

@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)

from src.models import (
    UserModel,
    TransactionModel,
    SessionModel,
    SavingsGoalModel,
    GoalContributionModel,
    CategoryModel,
    BudgetModel
)