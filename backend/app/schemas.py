from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str

    model_config = {
        "from_attributes": True
    }


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class OpportunityCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    opportunity_type: str = Field(min_length=2, max_length=100)
    location: str | None = Field(default=None, max_length=255)


class OpportunityUpdate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    opportunity_type: str = Field(min_length=2, max_length=100)
    location: str | None = Field(default=None, max_length=255)


class OpportunityResponse(BaseModel):
    id: int
    title: str
    description: str
    opportunity_type: str
    location: str | None
    status: str

    model_config = {
        "from_attributes": True
    }


class ApplicationResponse(BaseModel):
    id: int
    candidate_id: int
    opportunity_id: int
    status: str
    applied_at: datetime

    model_config = {
        "from_attributes": True
    }

class CandidateProfileCreate(BaseModel):
    phone: str | None = Field(default=None, max_length=30)
    education: str | None = Field(default=None, max_length=255)
    skills: str | None = None
    experience: str | None = None
    resume_path: str | None = Field(default=None, max_length=500)


class CandidateProfileResponse(BaseModel):
    id: int
    user_id: int
    phone: str | None
    education: str | None
    skills: str | None
    experience: str | None
    resume_path: str | None

    model_config = {
        "from_attributes": True
    }    

    
from pydantic import BaseModel

class ApplicationStatusUpdate(BaseModel):
    status: str


class InterviewCreate(BaseModel):
    application_id: int = Field(gt=0)
    interviewer_id: int = Field(gt=0)
    scheduled_at: datetime
    meeting_link: str | None = Field(default=None, max_length=1000)


class InterviewResponse(BaseModel):
    id: int
    application_id: int
    interviewer_id: int
    scheduled_at: datetime
    status: str
    meeting_link: str | None

    model_config = {"from_attributes": True}

class FeedbackCreate(BaseModel):
    technical_score: int = Field(ge=1, le=10)
    communication_score: int = Field(ge=1, le=10)
    problem_solving_score: int = Field(ge=1, le=10)
    comments: str = Field(min_length=5, max_length=5000)
    recommendation: str = Field(min_length=2, max_length=50)


class FeedbackResponse(BaseModel):
    id: int
    interview_id: int
    technical_score: int
    communication_score: int
    problem_solving_score: int
    comments: str
    recommendation: str
    created_at: datetime

    model_config = {"from_attributes": True}

