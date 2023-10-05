from datetime import datetime
from sqlalchemy import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column
from app.services.database.base import Base


class Washing(Base):
    __tablename__ = "washings"

    id: Mapped[str] = mapped_column(primary_key=True)
    terminal: Mapped[int]
    date: Mapped[datetime]
    start_date: Mapped[datetime] = mapped_column(nullable=True)
    end_date: Mapped[datetime] = mapped_column(nullable=True)
    mode: Mapped[int]
    phone: Mapped[str] = mapped_column(VARCHAR(12), nullable=True)
    bonuses: Mapped[int] = mapped_column(nullable=True)
    price: Mapped[float]

    def __repr__(self) -> str:
        return str(self.__dict__)
