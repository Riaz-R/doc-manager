from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from docmanager.db import Base


class Client(Base):
    """Someone the documents belong to. Clients come from the seed script for now."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    ref: Mapped[str] = mapped_column(unique=True)  # like "C-0042"
    name: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime]
