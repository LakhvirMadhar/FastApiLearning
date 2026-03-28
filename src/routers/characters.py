from typing import Optional

from fastapi import APIRouter, status

from src.schemas.characters import Character, CharacterResponse


router = APIRouter()


# Called a path parameter
@router.get("/{character_name}")
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
@router.get("/{character_name}/cards")
def get_character_cards(character_name: str, card_type: Optional[str] = None, energy: Optional[int] = None):
    return {
        "character": character_name,
        "card_type": card_type,
        "energy": energy
    }

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CharacterResponse)
def create_card_for_character(character: Character):
    """Create a new character with cards"""
    return {
        "character": character.name,
        "health": character.health,
        "cards": character.cards
    }