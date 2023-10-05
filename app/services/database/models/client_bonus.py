from sqlalchemy import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, validates
from app.services.database.base import Base


class ClientBonus(Base):
    """
    Implements table that represents Bonuses for clients getted by their phone
    """

    __tablename__ = "client_bonuses"

    phone: Mapped[str] = mapped_column(VARCHAR(12), primary_key=True)
    actual_amount: Mapped[int] = mapped_column(default=0)
    alltime_amount: Mapped[int] = mapped_column(default=0)

    @validates("actual_amount", "alltime_amount")
    def validate_actual_amount(self, key, amount):
        if amount < 0:
            raise ValueError("Amount of bonuses can't be < 0")
        return amount
