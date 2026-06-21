from pydantic import BaseModel
from typing import Optional

# ----- Auth Models -----
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# ----- User Info Response (for /api/me) -----
class UserResponse(BaseModel):
    username: str
    full_name: Optional[str] = None
    is_admin: bool

# ----- Admin Order Status Update -----
class OrderStatusUpdate(BaseModel):
    status: str   # e.g., "received", "printing", "completed", "picked"