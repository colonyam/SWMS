"""Reset or create the default admin user."""
import os
import sys

# Ensure backend root is on sys.path when run as a script
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.config import get_settings
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash


def main() -> None:
    settings = get_settings()
    print(f"Using DB: {settings.DATABASE_URL}")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "collins").first()
        if not user:
            user = db.query(User).filter(User.username == "admin").first()

        if not user:
            user = User(
                username="collins",
                email="collins@smartwaste.com",
                hashed_password=get_password_hash("colo1234"),
                full_name="Collins Admin",
                role=UserRole.ADMIN,
                is_active=True,
                is_superuser=True,
            )
            db.add(user)
        else:
            user.username = "collins"
            user.email = "collins@smartwaste.com"
            user.hashed_password = get_password_hash("colo1234")
            user.full_name = user.full_name or "Collins Admin"
            user.role = UserRole.ADMIN
            user.is_active = True
            user.is_superuser = True

        db.commit()
        user_count = db.query(User).count()
        print(f"Default user set to collins / colo1234 (users total: {user_count})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
