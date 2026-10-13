
from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User, UserRole
from app.security import hash_password


def main():
    full_name = input("Staff full name: ").strip()
    email = input("Staff email: ").strip().lower()

    if not full_name or not email:
        print("Name and email are required.")
        return

    password = getpass("Staff password: ")
    confirm_password = getpass("Confirm staff password: ")

    if len(password) < 12:
        print("Password must be at least 12 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    with SessionLocal() as db:
        try:
            existing_user = db.scalar(
                select(User).where(User.email == email)
            )

            if existing_user:
                print(
                    "An account with this email already exists. "
                    "No changes were made."
                )
                return

            staff_user = User(
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                role=UserRole.STAFF,
            )

            db.add(staff_user)
            db.commit()
            db.refresh(staff_user)

            print("Staff account created successfully.")
            print(f"User ID: {staff_user.id}")
            print(f"Email: {staff_user.email}")
            print(f"Role: {staff_user.role.value}")

        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    main()
