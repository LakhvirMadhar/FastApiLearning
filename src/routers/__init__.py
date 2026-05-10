from fastapi import APIRouter

from src.routers import cards, neow, characters, test_routes, chest

api_router = APIRouter()

api_router.include_router(cards.router)
api_router.include_router(neow.router)
api_router.include_router(characters.router)
api_router.include_router(test_routes.router)
api_router.include_router(chest.router)
