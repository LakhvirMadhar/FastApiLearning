from fastapi import (
    APIRouter,
    BackgroundTasks,
)

router = APIRouter(tags=["Chest"])


# Pretend this was an important function
# W/ background tasks, this would be kicked off after the endpoint is called
# But meant for lightweight tasks
def print_log(message: str):
    print(message)


@router.get("/chest")
def open_chest(background_tasks: BackgroundTasks):
    background_tasks.add_task(print_log, "You got a new loot box!")
    return {"message": "Opened Chest"}
