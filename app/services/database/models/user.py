from datetime import datetime
from sqlalchemy import VARCHAR, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.services.database.base import Base


class User(Base):
    """
    Implements base table for all registered in bot users
    phone_number format: +79091234567
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    first_name: Mapped[str]
    last_name: Mapped[str] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(VARCHAR(12), nullable=True)
    registration_date: Mapped[datetime] = mapped_column(default=datetime.now)
