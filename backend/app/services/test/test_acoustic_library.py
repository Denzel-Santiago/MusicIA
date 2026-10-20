from app.database.connection import SessionLocal
from app.services.acoustic_library import fingerprint_library


def main() -> None:
    db = SessionLocal()

    try:
        fingerprint_library(db)

    finally:
        db.close()


if __name__ == "__main__":
    main()