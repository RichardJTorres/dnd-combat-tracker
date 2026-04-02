from sqlmodel import SQLModel, create_engine, Session

from dnd_combat_tracker.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Create all tables if they don't exist."""
    # Import models so SQLModel registers them before create_all
    import dnd_combat_tracker.db.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
