from app.database import SessionLocal
from app.migration import migrate_justification, migrate_mini_crm


def main() -> None:
    db = SessionLocal()
    try:
        mini_result = migrate_mini_crm(db)
        justification_result = migrate_justification(db)
        print("Mini CRM:", mini_result)
        print("Justification:", justification_result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
