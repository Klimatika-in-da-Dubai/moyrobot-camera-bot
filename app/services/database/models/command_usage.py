from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.services.database.base import Base


class CommandUsage(Base):
    __tablename__ = "commands_usages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    usage_timestamp: Mapped[datetime] = mapped_column(default=datetime.now)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    command: Mapped[str]
