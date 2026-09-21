"""Pydantic schemas for users and authentication."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    display_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    consent_training: bool = False


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    is_active: bool
    consent_training: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
