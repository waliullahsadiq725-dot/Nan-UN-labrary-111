from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Literal

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["student", "teacher"]
    department: str | None = Field(default=None, max_length=120)
    student_or_staff_id: str | None = Field(default=None, max_length=60)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    role: str
    department: str | None
    student_or_staff_id: str | None
    is_active: bool
    created_at: datetime

class DocumentOut(BaseModel):
    id: int
    title: str
    description: str | None
    category: str
    department: str | None
    subject: str | None
    visibility: str
    original_filename: str
    file_size: int
    downloads: int
    is_approved: bool
    uploader_name: str
    uploader_role: str
    created_at: datetime
    is_owner: bool
    is_bookmarked: bool = False

class UserStatusIn(BaseModel):
    is_active: bool

class DocumentApprovalIn(BaseModel):
    is_approved: bool

class ReportIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)
