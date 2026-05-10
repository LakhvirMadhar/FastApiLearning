from fastapi import FastAPI

from src import models  # noqa: F401
from src.config import settings
from src.database import Base, engine
from src.routers import api_router

app = FastAPI()

app.include_router(api_router)


# Route decorator - connects URL path (i.e. endpoint) to a python function
# "/" is root URL
@app.get("/")
def root():
    return {"message": "hello world"}


@app.get("/about")
def about():
    return {"message": "This is my first FastAPI application"}


@app.get("/info")
def app_info():
    return {"app_name": settings.app_name, "debug": settings.debug}


Base.metadata.create_all(bind=engine)
