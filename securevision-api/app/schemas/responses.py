from pydantic import BaseModel

class APIResponse(BaseModel):
    """Base response model for API messages"""
    status: str
    message: str
