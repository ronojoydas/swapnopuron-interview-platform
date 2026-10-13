from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Candidate, User, UserRole
from app.schemas import CandidateProfileCreate, CandidateProfileResponse


router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"]
)


@router.post(
    "/me",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_201_CREATED
)
def create_candidate_profile(
    profile_data: CandidateProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can create candidate profiles"
        )

    existing_profile = db.scalar(
        select(Candidate).where(
            Candidate.user_id == current_user.id
        )
    )

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate profile already exists"
        )

    candidate = Candidate(
        user_id=current_user.id,
        phone=profile_data.phone,
        education=profile_data.education,
        skills=profile_data.skills,
        experience=profile_data.experience,
        resume_path=profile_data.resume_path
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return candidate