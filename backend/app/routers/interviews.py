
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import (
    Application,
    ApplicationStatus,
    Candidate,
    Interview,
    InterviewStatus,
    User,
    UserRole,
)
from app.schemas import InterviewCreate, InterviewResponse


router = APIRouter(
    prefix="/interviews",
    tags=["Interviews"],
)


@router.post(
    "",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def schedule_interview(
    interview_data: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only staff and admins can schedule interviews.
    if current_user.role not in (UserRole.ADMIN, UserRole.STAFF):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff and admins can schedule interviews",
        )

    # Check that the application exists.
    application = db.get(Application, interview_data.application_id)

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    # An interview can only be scheduled for an application in the interview stage.
    if application.status != ApplicationStatus.INTERVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application must be in interview status before scheduling",
        )

    # Check that the assigned interviewer exists.
    interviewer = db.get(User, interview_data.interviewer_id)

    if interviewer is None or interviewer.role != UserRole.INTERVIEWER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The assigned user must have the interviewer role",
        )

    # Require a future interview time.
    scheduled_at = interview_data.scheduled_at

    if scheduled_at.tzinfo is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="scheduled_at must include a timezone, such as +05:30",
        )

    if scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview must be scheduled for a future time",
        )

    interview = Interview(
        application_id=interview_data.application_id,
        interviewer_id=interview_data.interviewer_id,
        scheduled_at=scheduled_at,
        status=InterviewStatus.SCHEDULED,
        meeting_link=interview_data.meeting_link,
    )

    db.add(interview)
    db.commit()
    db.refresh(interview)

    return interview


@router.get(
    "",
    response_model=list[InterviewResponse],
)
def list_interviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Staff and admins can view all interviews.
    if current_user.role in (UserRole.ADMIN, UserRole.STAFF):
        interviews = db.scalars(
            select(Interview).order_by(Interview.scheduled_at.asc())
        ).all()
        return list(interviews)

    # Interviewers can view only interviews assigned to them.
    if current_user.role == UserRole.INTERVIEWER:
        interviews = db.scalars(
            select(Interview)
            .where(Interview.interviewer_id == current_user.id)
            .order_by(Interview.scheduled_at.asc())
        ).all()
        return list(interviews)

    # Candidates can view interviews linked to their own applications.
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

        interviews = db.scalars(
            select(Interview)
            .join(
                Application,
                Interview.application_id == Application.id,
            )
            .where(Application.candidate_id == candidate.id)
            .order_by(Interview.scheduled_at.asc())
        ).all()

        return list(interviews)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not permitted to view interviews",
    )


@router.patch(
    "/{interview_id}/status",
    response_model=InterviewResponse,
)
def update_interview_status(
    interview_id: int,
    status_value: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only staff and admins can update interview status.
    if current_user.role not in (
        UserRole.ADMIN,
        UserRole.STAFF,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff and admins can update interview status",
        )

    interview = db.get(Interview, interview_id)

    if interview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )

    allowed_statuses = {item.value for item in InterviewStatus}

    if status_value not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Invalid status. Allowed values: "
                + ", ".join(sorted(allowed_statuses))
            ),
        )

    interview.status = InterviewStatus(status_value)

    db.commit()
    db.refresh(interview)

    return interview
