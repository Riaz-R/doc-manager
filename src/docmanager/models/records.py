from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from docmanager.db import Base


class StateChange(Base):
    """One row of history for every move a Page or Document makes. Never edited."""

    __tablename__ = "state_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    object_kind: Mapped[str]  # "page" or "document"
    object_id: Mapped[int]
    action: Mapped[str]
    from_state: Mapped[str | None]  # None for "(new)"
    to_state: Mapped[str | None]  # None for "(row deleted)"
    at: Mapped[datetime]
    note: Mapped[str | None]
