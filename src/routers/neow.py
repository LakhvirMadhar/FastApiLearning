from fastapi import APIRouter

from src.schemas.neow import BlessingResponse

router = APIRouter(prefix="/neow", tags=["Neow"])


@router.get("/blessings", response_model=list[BlessingResponse])
def neow_blessing():
    """"""
    blessings = [
        {
            "blessing_name": "Gain 100 Gold",
            "blessing_description": "Receive 100 gold",
            "blessing_secret": "bonus_tier_1",
        },
        {
            "blessing_name": "Random Rare Card",
            "blessing_description": "Obtain a random rare card",
            "blessing_secret": "bonus_tier_2",
        },
    ]

    return blessings
