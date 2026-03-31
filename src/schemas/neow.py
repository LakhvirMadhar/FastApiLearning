from pydantic import BaseModel


class BlessingResponse(BaseModel):
    """Define what blessing to return"""

    blessing_name: str
