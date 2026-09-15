import secrets

from src.database import SessionLocal
from src.models import UserModel
from src.services.auth_service import hash_access_key


def main():
    db = SessionLocal()

    try:
        name = input("Username: ").strip()

        access_key = secrets.token_urlsafe(32)
        hashed_key = hash_access_key(access_key)

        user = UserModel(
            name=name,
            hashed_access_key=hashed_key
        )

        db.add(user)
        db.commit()

        print("\nUser created successfully.")
        print(f"Username: {name}")
        print(f"Access key: {access_key}")
        print("\nSAVE THIS KEY. It cannot be recovered from the database.")

    finally:
        db.close()


if __name__ == "__main__":
    main()