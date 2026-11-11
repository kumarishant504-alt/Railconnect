from sqlmodel import SQLModel
from app.database.engine import engine
from app.models import user, station, train, booking, payment  # noqa: F401


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def seed_admin():
    from sqlmodel import Session, select
    from app.models.user import User
    from app.utils.security import hash_password
    from app.config import get_settings

    settings = get_settings()
    with Session(engine) as session:
        existing = session.exec(
            select(User).where(User.email == settings.admin_email)
        ).first()
        if not existing:
            admin = User(
                full_name="System Administrator",
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
                role="admin",
                is_active=True,
            )
            session.add(admin)
            session.commit()
            print(f"[RailConnect] Admin seeded: {settings.admin_email}")
        else:
            print(f"[RailConnect] Admin already exists: {settings.admin_email}")
