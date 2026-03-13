from typing import Annotated, Optional
from datetime import datetime, timezone
from beanie import Document, Indexed
from pydantic import EmailStr, Field

class User(Document):
    # Using the modern Annotated syntax for Beanie/Pydantic
    email: Annotated[EmailStr, Indexed(unique=True)]
    username: Annotated[str, Indexed(unique=True)] 
    # REMOVED the old line here that was causing the error
    
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        # Since you indexed them above, you don't strictly need them here, 
        # but it doesn't hurt.
        indexes = ["email", "username"]

    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@example.com",
                "username": "john_doe",
                "full_name": "John Doe",
            }
        }