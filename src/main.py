from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum

app = FastAPI()

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

class Character(BaseModel):
    name: str
    health: int
    cards: list[Card]

class CardResponse(BaseModel):
    """Define what API returns"""
    name: str
    card_type: CardType
    energy: int


# Route decorator - connects URL path (i.e. endpoint) to a python function
# "/" is root URL
@app.get("/")
def root():
    return {"message": "hello world"}


@app.get("/about")
def about():
    return {"message": "This is my first FastAPI application"}


# Called a query parameter
# For routes, it's good practice to put the base route first, just like when making python functions
@app.get("/cards")
def get_items_query(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}


@app.post("/cards")
def create_card(card: Card):
    return {"message": f"Created card: {card.name}", "card": card}

# Although we sent the entire card, the model will only return the fields inside CardResponse
@app.post("/cards/preview", response_model=CardResponse)
def preview_card(card:Card):
    return card

# Called a path parameter
@app.get("/character/{character_name}")
def get_items(character_name: str):
    """Checks if a character is playable in Slay the Spire."""
    playable_characters = ["Ironclad", "Silent", "Watcher", "Defect"]
    message = "{character_name} is {playable_status}a playable character in Slay the Spire"
    character_name = character_name.split()[-1].title()
    
    if character_name in playable_characters:
        message = message.format(character_name=character_name, playable_status="")
    else:
        message = message.format(character_name=character_name, playable_status="not ")


    return {"message": message}


# Combine path and query parameter
@app.get("/characters/{character_name}/cards")
def get_character_cards(character_name: str, card_type: Optional[str] = None, energy: Optional[int] = None):
    return {
        "character": character_name,
        "card_type": card_type,
        "energy": energy
    }

@app.post("/characters/")
def create_card_for_character(character: Character):
    """Create a new character with cards"""
    return {
        "character": character.name,
        "health": character.health,
        "cards": character.cards
    }