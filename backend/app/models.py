from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    INTERVIEWER = "interviewer"
    CANDIDATE = "candidate"


class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    SCREENING = "screening"
    SHORTLISTED = "shortlisted"
    INTERVIEW = "interview"
    SELECTED = "selected"
    REJECTED = "rejected"


class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(default=UserRole.CANDIDATE)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    candidate_profile: Mapped["Candidate | None"] = relationship(
        back_populates="user",
        uselist=False
    )


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True
    )
    phone: Mapped[str | None] = mapped_column(String(30))
    education: Mapped[str | None] = mapped_column(String(255))
    skills: Mapped[str | None] = mapped_column(Text)
    experience: Mapped[str | None] = mapped_column(Text)
    resume_path: Mapped[str | None] = mapped_column(String(500))

    user: Mapped["User"] = relationship(
        back_populates="candidate_profile"
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="candidate"
    )


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    opportunity_type: Mapped[str] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(30),
        default="open"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="opportunity"
    )


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id")
    )
    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("opportunities.id")
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        default=ApplicationStatus.APPLIED
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    candidate: Mapped["Candidate"] = relationship(
        back_populates="applications"
    )

    opportunity: Mapped["Opportunity"] = relationship(
        back_populates="applications"
    )

    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="application"
    )


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id")
    )
    interviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )
    scheduled_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True)
)
    status: Mapped[InterviewStatus] = mapped_column(
        default=InterviewStatus.SCHEDULED
    )
    meeting_link: Mapped[str | None] = mapped_column(String(500))

    application: Mapped["Application"] = relationship(
        back_populates="interviews"
    )

    interviewer: Mapped["User"] = relationship()


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interviews.id"),
        unique=True
    )
    technical_score: Mapped[int | None]
    communication_score: Mapped[int | None]
    problem_solving_score: Mapped[int | None]
    comments: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )