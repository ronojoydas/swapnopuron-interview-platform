

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


def require_candidate(current_user: User) -> None:
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can manage candidate profiles"
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
    require_candidate(current_user)

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


@router.get(
    "/me",
    response_model=CandidateProfileResponse
)
def get_candidate_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_candidate(current_user)

    candidate = db.scalar(
        select(Candidate).where(
            Candidate.user_id == current_user.id
        )
    )

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )

    return candidate


@router.put(
    "/me",
    response_model=CandidateProfileResponse
)
def update_candidate_profile(
    profile_data: CandidateProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_candidate(current_user)

    candidate = db.scalar(
        select(Candidate).where(
            Candidate.user_id == current_user.id
        )
    )

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found"
        )

    candidate.phone = profile_data.phone
    candidate.education = profile_data.education
    candidate.skills = profile_data.skills
    candidate.experience = profile_data.experience
    candidate.resume_path = profile_data.resume_path

    db.commit()
    db.refresh(candidate)

    return candidate
