from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import Opportunity, User, UserRole
from app.schemas import (
    OpportunityCreate,
    OpportunityResponse,
    OpportunityUpdate,
)


router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"]
)


@router.post(
    "",
    response_model=OpportunityResponse,
    status_code=status.HTTP_201_CREATED
)
def create_opportunity(
    opportunity_data: OpportunityCreate,
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.STAFF
        )
    ),
    db: Session = Depends(get_db)
):
    opportunity = Opportunity(
        title=opportunity_data.title,
        description=opportunity_data.description,
        opportunity_type=opportunity_data.opportunity_type,
        location=opportunity_data.location,
        status="open"
    )

    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)

    return opportunity


@router.get(
    "",
    response_model=list[OpportunityResponse]
)
def list_opportunities(
    db: Session = Depends(get_db)
):
    opportunities = db.scalars(
        select(Opportunity)
        .order_by(Opportunity.created_at.desc())
    ).all()

    return opportunities


@router.get(
    "/{opportunity_id}",
    response_model=OpportunityResponse
)
def get_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db)
):
    opportunity = db.scalar(
        select(Opportunity).where(
            Opportunity.id == opportunity_id
        )
    )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )

    return opportunity


@router.put(
    "/{opportunity_id}",
    response_model=OpportunityResponse
)
def update_opportunity(
    opportunity_id: int,
    opportunity_data: OpportunityUpdate,
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.STAFF
        )
    ),
    db: Session = Depends(get_db)
):
    opportunity = db.scalar(
        select(Opportunity).where(
            Opportunity.id == opportunity_id
        )
    )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )

    opportunity.title = opportunity_data.title
    opportunity.description = opportunity_data.description
    opportunity.opportunity_type = opportunity_data.opportunity_type
    opportunity.location = opportunity_data.location

    db.commit()
    db.refresh(opportunity)

    return opportunity


@router.patch(
    "/{opportunity_id}/close",
    response_model=OpportunityResponse
)
def close_opportunity(
    opportunity_id: int,
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.STAFF
        )
    ),
    db: Session = Depends(get_db)
):
    opportunity = db.scalar(
        select(Opportunity).where(
            Opportunity.id == opportunity_id
        )
    )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )

    if opportunity.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Opportunity is already closed"
        )

    opportunity.status = "closed"

    db.commit()
    db.refresh(opportunity)

    return opportunity