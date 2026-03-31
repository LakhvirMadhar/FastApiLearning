from fastapi import (
    FastAPI,
    Depends,
)

from src.routers.cards import router as cards_router
from src.routers.neow import router as neow_router
from src.routers.characters import router as character_router
from src.dependencies.time_logger import get_datetime

app = FastAPI()

app.include_router(
    cards_router, prefix="/cards", tags=["Cards"], dependencies=[Depends(get_datetime)]
)
app.include_router(neow_router, prefix="/neow", tags=["Neow"])
app.include_router(character_router, prefix="/character", tags=["Character"])


# Route decorator - connects URL path (i.e. endpoint) to a python function
# "/" is root URL
@app.get("/")
def root():
    return {"message": "hello world"}


@app.get("/about")
def about():
    return {"message": "This is my first FastAPI application"}
