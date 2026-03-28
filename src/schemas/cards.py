from enum import Enum
from typing import Optional

from pydantic import BaseModel


class CardType(str, Enum):
    """The type of the card"""
    ATTACK = "attack"
    SKILL = "skill"
    POWER = "power"
    STATUS = "status"
    CURSE = "curse"


class Card(BaseModel):
    name: str
    energy: int
    card_type: CardType
    damage: int
    description: Optional[str] = None


class CardResponse(BaseModel):
    """Define what API returns"""
    name: str
    card_type: CardType
    energy: int