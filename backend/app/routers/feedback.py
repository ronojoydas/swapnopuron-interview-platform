
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import (
    Feedback,
    Interview,
    InterviewStatus,
    User,
    UserRole,
)
from app.schemas import FeedbackCreate, FeedbackResponse


router = APIRouter(
    prefix="/feedback",
    tags=["Interview Feedback"],
)


@router.post(
    "/{interview_id}",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_feedback(
    interview_id: int,
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only interviewers and admins may submit feedback.
    if current_user.role not in (
        UserRole.INTERVIEWER,
        UserRole.ADMIN,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only interviewers and admins can submit feedback",
        )

    interview = db.get(Interview, interview_id)

    if interview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )

    # Interviewers may submit feedback only for their own assignments.
    if (
        current_user.role == UserRole.INTERVIEWER
        and interview.interviewer_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit feedback for your assigned interviews",
        )

    # Feedback is accepted only after the interview is completed.
    if interview.status != InterviewStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mark the interview as completed before submitting feedback",
        )

    existing_feedback = db.scalar(
        select(Feedback).where(
            Feedback.interview_id == interview_id
        )
    )

    if existing_feedback is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback has already been submitted for this interview",
        )

    feedback = Feedback(
        interview_id=interview_id,
        technical_score=feedback_data.technical_score,
        communication_score=feedback_data.communication_score,
        problem_solving_score=feedback_data.problem_solving_score,
        comments=feedback_data.comments,
        recommendation=feedback_data.recommendation,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback


@router.get(
    "/{interview_id}",
    response_model=FeedbackResponse,
)
def get_feedback(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interview = db.get(Interview, interview_id)

    if interview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )

    # Only staff/admins and the assigned interviewer can view feedback.
    permitted = current_user.role in (
        UserRole.ADMIN,
        UserRole.STAFF,
    ) or (
        current_user.role == UserRole.INTERVIEWER
        and interview.interviewer_id == current_user.id
    )

    if not permitted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not permitted to view this feedback",
        )

    feedback = db.scalar(
        select(Feedback).where(
            Feedback.interview_id == interview_id
        )
    )

    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback has not been submitted yet",
        )

    return feedback
