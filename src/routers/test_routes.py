import time
import asyncio

from fastapi import APIRouter

router = APIRouter(tags=["Test"])


# BAD - blocks the event loop, freezes the server
@router.get("/slow-async-bad")
async def slow_route_async_bad():
    time.sleep(5)
    return {"message": "done"}


@router.get("/slow-async-good")
async def slow_route_async_good():
    await asyncio.sleep(5)
    return {"message": "done"}


@router.get("/slow-sync")
def slow_route_sync():
    time.sleep(5)
    return {"message": "done"}
