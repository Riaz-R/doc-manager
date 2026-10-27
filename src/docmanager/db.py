from flask import Flask, current_app, g
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Every database model inherits from this."""


def init_db(app: Flask, db_path) -> None:
    """Create the engine and any missing tables, and close sessions after each request."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    app.extensions["docmanager_engine"] = engine
    app.extensions["docmanager_sessions"] = sessionmaker(engine)

    @app.teardown_appcontext
    def close_session(_exception):
        session = g.pop("db_session", None)
        if session is not None:
            session.close()


def get_session() -> Session:
    """The one database session for this request, made on first use."""
    if "db_session" not in g:
        g.db_session = current_app.extensions["docmanager_sessions"]()
    return g.db_session
