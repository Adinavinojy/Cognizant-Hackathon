"""
Router: /roles
Endpoints for fetching and classifying job roles.
"""

import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.role_topic import JobRole, Topic
from app.schemas.roles import JobRoleOut, ClassifyRoleRequest, ClassifyRoleResponse
from app.services.role_classifier import classify_custom_role

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=List[JobRoleOut])
def get_roles(db: Session = Depends(get_db)) -> List[JobRoleOut]:
    """
    Returns all predefined job roles and their associated default tech stack topics.
    """
    roles = db.query(JobRole).filter(JobRole.is_custom == False).options(joinedload(JobRole.topics)).all()
    return roles


@router.post("/classify", response_model=ClassifyRoleResponse)
def classify_role(payload: ClassifyRoleRequest, db: Session = Depends(get_db)) -> ClassifyRoleResponse:
    """
    Classifies a custom job role string to the nearest predefined role.
    If it maps successfully, it creates (or finds) the custom role in the DB
    mapped to the predefined one.
    """
    # 1. Fetch predefined role names
    predefined_roles = db.query(JobRole).filter(JobRole.is_custom == False).all()
    role_names = [r.role_name for r in predefined_roles]

    if not role_names:
        return ClassifyRoleResponse(custom_role=payload.custom_role, mapped_role=None)

    # 2. Check if this exact custom string is already in the DB as a custom role
    existing_custom = db.query(JobRole).filter(
        JobRole.is_custom == True,
        JobRole.role_name == payload.custom_role
    ).options(joinedload(JobRole.topics)).first()
    
    if existing_custom and existing_custom.mapped_to_role_id:
        mapped_target = db.get(JobRole, existing_custom.mapped_to_role_id)
        if mapped_target:
            # We return the mapped target (the predefined role) so the frontend 
            # gets the full tech stack
            mapped_target_with_topics = db.query(JobRole).filter(
                JobRole.role_id == mapped_target.role_id
            ).options(joinedload(JobRole.topics)).first()
            return ClassifyRoleResponse(custom_role=payload.custom_role, mapped_role=mapped_target_with_topics)

    # 3. Use LLM to classify
    mapped_name = classify_custom_role(payload.custom_role, role_names)
    
    if not mapped_name:
        return ClassifyRoleResponse(custom_role=payload.custom_role, mapped_role=None)

    # 4. Find the mapped predefined role in DB
    target_role = next((r for r in predefined_roles if r.role_name == mapped_name), None)
    
    if target_role:
        # Save this mapping so we don't have to query the LLM again for the same string
        if not existing_custom:
            new_custom = JobRole(
                role_id=uuid.uuid4(),
                role_name=payload.custom_role,
                is_custom=True,
                mapped_to_role_id=target_role.role_id
            )
            db.add(new_custom)
            db.commit()

        # Return the target role with its topics
        target_role_with_topics = db.query(JobRole).filter(
            JobRole.role_id == target_role.role_id
        ).options(joinedload(JobRole.topics)).first()

        return ClassifyRoleResponse(custom_role=payload.custom_role, mapped_role=target_role_with_topics)

    return ClassifyRoleResponse(custom_role=payload.custom_role, mapped_role=None)
