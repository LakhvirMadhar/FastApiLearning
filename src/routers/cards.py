from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
)

from src.schemas.cards import (
    Card,
    CardResponse,
)
from src.dependencies.pagination import (
    PaginationParams,
    validated_pagination,
)

router = APIRouter()

cards = {
    "1": {"name": "Strike", "energy": 1, "card_type": "attack"},
    "2": {"name": "Defend", "energy": 1, "card_type": "skill"},
}


# Called a query parameter
# For routes, it's good practice to put the base route first, just like when making python functions
@router.get("/", response_model=list[CardResponse])
async def get_cards(pagination: PaginationParams = Depends(validated_pagination)):
    cards = [
        {"name": "Strike", "energy": 1, "card_type": "attack", "damage": 6},
        {"name": "Bowling Ball", "energy": 1, "card_type": "attack", "damage": 6},
    ]
    return cards[pagination.skip : pagination.skip + pagination.limit]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_card(card: Card):
    if card.name in [card["name"] for card in cards.values()]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Card '{card.name} already exists'",
        )
    return {"message": f"Created card: {card.name}", "card": card}


@router.get("/{card_id}")
def get_card(card_id: str):
    if card_id not in cards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Card not found",
                "card_id": card_id,
                "suggestion": "Use GET /cards to see available cards",
            },
        )

    return cards[card_id]


# Although we sent the entire card, the model will only return the fields inside CardResponse
@router.post(
    "/preview", response_model=CardResponse, status_code=status.HTTP_201_CREATED
)
def preview_card(card: Card):
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int):
    # find card in database to then delete
    return None


@router.put("/{card_id}", status_code=status.HTTP_200_OK)
def update_card(card: Card, card_id: int):
    # Again, database logic here
    return {"card": card, "card_id": card_id}
