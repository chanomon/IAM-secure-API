from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class PermissionOut(BaseModel):
    id: int
    name: str
    resource: str
    action: str

class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    permissions: List[PermissionOut] = []

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    roles: List[RoleOut] = []
    metadata_json: Optional[dict]

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class RoleAssignment(BaseModel):
    user_id: int
    role_id: int
