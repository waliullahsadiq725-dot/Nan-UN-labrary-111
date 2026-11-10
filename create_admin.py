from .database import Base, engine, SessionLocal
from .models import User
from .security import hash_password
from .config import settings

def main():
    Base.metadata.create_all(bind=engine)
    if len(settings.secret_key) < 32 or settings.secret_key.startswith("CHANGE_"):
        raise SystemExit("Set a strong SECRET_KEY in .env before creating admin.")
    if len(settings.admin_password) < 12 or settings.admin_password.startswith("CHANGE_"):
        raise SystemExit("Set ADMIN_PASSWORD (at least 12 characters) in .env.")
    db = SessionLocal()
    try:
        email = settings.admin_email.lower()
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"Account already exists: {email}")
            return
        admin = User(full_name=settings.admin_name, email=email,
                     password_hash=hash_password(settings.admin_password),
                     role="admin", is_active=True)
        db.add(admin); db.commit()
        print(f"Administrator created: {email}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
