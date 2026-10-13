
from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User, UserRole
from app.security import hash_password


def main():
    email = input("Candidate email to reset: ").strip().lower()

    if not email:
        print("Email is required.")
        return

    new_password = getpass("Enter new candidate password: ")

    if len(new_password) < 12:
        print("Password must be at least 12 characters.")
        return

    confirm_password = getpass("Confirm new candidate password: ")

    if new_password != confirm_password:
        print("Passwords do not match. Nothing changed.")
        return

    with SessionLocal() as db:
        try:
            user = db.scalar(
                select(User).where(User.email == email)
            )

            if user is None:
                print("Account not found.")
                return

            if user.role != UserRole.CANDIDATE:
                print("Account is not a candidate. Nothing changed.")
                return

            user.password_hash = hash_password(new_password)
            db.commit()

            print("Candidate password reset successfully.")
            print(f"Email: {user.email}")
            print(f"User ID: {user.id}")

        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    main()
