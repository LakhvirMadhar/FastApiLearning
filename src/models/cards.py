from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Card(Base):
    __tablename__ = "Cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500))
