from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.services.database.base import Base


class Permission(Base):
    """Implements permissions of the roles"""

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str]
