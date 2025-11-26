from sqlalchemy import Engine, text, inspect


def ensure_schema_up_to_date(engine: Engine) -> None:
    """Ensure DB schema is aligned with the current ORM models.

    This is a lightweight, non-destructive shim for SQLite that only adds
    missing columns to existing tables. It never drops or alters existing
    columns, so existing data remains intact.
    """

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "client" not in tables:
        # Nothing to do yet – tables will be created by Base.metadata.create_all
        return

    existing_cols = {col["name"] for col in inspector.get_columns("client")}

    ddl_statements: list[str] = []

    # New personal / employment / address fields added to Client model
    if "birth_country" not in existing_cols:
        ddl_statements.append("ALTER TABLE client ADD COLUMN birth_country TEXT")
    if "employer_name" not in existing_cols:
        ddl_statements.append("ALTER TABLE client ADD COLUMN employer_name TEXT")
    if "employer_hp" not in existing_cols:
        ddl_statements.append("ALTER TABLE client ADD COLUMN employer_hp TEXT")
    if "employer_address" not in existing_cols:
        ddl_statements.append("ALTER TABLE client ADD COLUMN employer_address TEXT")
    if "employer_phone" not in existing_cols:
        ddl_statements.append("ALTER TABLE client ADD COLUMN employer_phone TEXT")
    if "address_house_number" not in existing_cols:
        ddl_statements.append("ALTER TABLE client ADD COLUMN address_house_number TEXT")
    if "address_apartment" not in existing_cols:
        ddl_statements.append("ALTER TABLE client ADD COLUMN address_apartment TEXT")

    if not ddl_statements:
        return

    # Apply all pending ALTER TABLE statements in a single transaction
    with engine.begin() as connection:
        for ddl in ddl_statements:
            connection.execute(text(ddl))
