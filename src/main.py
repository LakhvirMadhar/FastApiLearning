from typing import Optional
from fastapi import FastAPI

app = FastAPI()


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