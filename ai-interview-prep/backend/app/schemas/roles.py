"""
Pydantic schemas for /roles endpoints.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class TopicOut(BaseModel):
    topic_id: UUID
    role_id: UUID
    topic_name: str
    category: Optional[str] = None

    model_config = {"from_attributes": True}


class JobRoleOut(BaseModel):
    role_id: UUID
    role_name: str
    description: Optional[str] = None
    is_custom: bool
    mapped_to_role_id: Optional[UUID] = None
    
    topics: List[TopicOut] = []

    model_config = {"from_attributes": True}


class ClassifyRoleRequest(BaseModel):
    custom_role: str


class ClassifyRoleResponse(BaseModel):
    custom_role: str
    mapped_role: Optional[JobRoleOut] = None
