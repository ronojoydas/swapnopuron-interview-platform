
from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User, UserRole
from app.security import password_hash


def main():
    email = input("Interviewer email: ").strip().lower()
    full_name = input("Interviewer full name: ").strip()

    if not email or not full_name:
        print("Email and full name are required.")
        return

    password = getpass("Set interviewer password: ")
    confirm_password = getpass("Confirm interviewer password: ")

    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    with SessionLocal() as db:
        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            print(
                "An account with this email already exists. "
                f"Existing role: {existing_user.role.value}"
            )
            print("No account was changed.")
            return

        interviewer = User(
            full_name=full_name,
            email=email,
            password_hash=password_hash.hash(password),
            role=UserRole.INTERVIEWER,
        )

        db.add(interviewer)
        db.commit()
        db.refresh(interviewer)

        print("\nInterviewer account created successfully.")
        print(f"User ID: {interviewer.id}")
        print(f"Email: {interviewer.email}")
        print(f"Role: {interviewer.role.value}")


if __name__ == "__main__":
    main()
