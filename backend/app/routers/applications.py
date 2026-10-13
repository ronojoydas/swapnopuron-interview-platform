
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import (
    Application,
    ApplicationStatus,
    Candidate,
    Opportunity,
    User,
    UserRole,
)
from app.schemas import ApplicationResponse, ApplicationStatusUpdate


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post(
    "/{opportunity_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_for_opportunity(
    opportunity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can apply for opportunities",
        )

    candidate = db.scalar(
        select(Candidate).where(
            Candidate.user_id == current_user.id
        )
    )

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found. Create your profile first.",
        )

    opportunity = db.get(Opportunity, opportunity_id)

    if opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    if opportunity.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This opportunity is closed and no longer accepting applications",
        )

    existing_application = db.scalar(
        select(Application).where(
            Application.candidate_id == candidate.id,
            Application.opportunity_id == opportunity.id,
        )
    )

    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied for this opportunity",
        )

    application = Application(
        candidate_id=candidate.id,
        opportunity_id=opportunity.id,
        status=ApplicationStatus.APPLIED,
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return application


@router.get(
    "/me",
    response_model=list[ApplicationResponse],
)
def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can view their own applications here",
        )

    candidate = db.scalar(
        select(Candidate).where(
            Candidate.user_id == current_user.id
        )
    )

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found",
        )

    applications = db.scalars(
        select(Application)
        .where(Application.candidate_id == candidate.id)
        .order_by(Application.applied_at.desc())
    ).all()

    return list(applications)


@router.get(
    "",
    response_model=list[ApplicationResponse],
)
def get_all_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in (
        UserRole.ADMIN,
        UserRole.STAFF,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff and admins can view all applications",
        )

    applications = db.scalars(
        select(Application).order_by(
            Application.applied_at.desc()
        )
    ).all()

    return list(applications)


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
)
def update_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in (
        UserRole.ADMIN,
        UserRole.STAFF,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff and admins can update application status",
        )

    application = db.get(Application, application_id)

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    allowed_statuses = {
        item.value for item in ApplicationStatus
    }

    if status_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Invalid status. Allowed values: "
                + ", ".join(sorted(allowed_statuses))
            ),
        )

    application.status = ApplicationStatus(status_data.status)

    db.commit()
    db.refresh(application)

    return application


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def get_application_details(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = db.get(Application, application_id)

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    # Staff and admins can view any application.
    if current_user.role in (
        UserRole.ADMIN,
        UserRole.STAFF,
    ):
        return application

    # Candidates can view only their own applications.
    if current_user.role == UserRole.CANDIDATE:
        candidate = db.scalar(
            select(Candidate).where(
                Candidate.user_id == current_user.id
            )
        )

        if candidate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found",
            )

        if application.candidate_id != candidate.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own applications",
            )

        return application

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not permitted to view this application",
    )
