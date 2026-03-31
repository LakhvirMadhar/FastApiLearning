from pydantic import BaseModel

from .cards import Card


class Character(BaseModel):
    name: str
    health: int
    cards: list[Card]


class CharacterResponse(BaseModel):
    character: str
