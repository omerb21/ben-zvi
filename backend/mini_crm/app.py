from pathlib import Path
from datetime import date
import sqlite3, pandas as pd
from flask import Flask, request, redirect, url_for, render_template, jsonify, current_app
import tempfile
from crm_ingestion.utils.source_names import get_source_display_name
from services.upload_service import UploadProcessingError, transform_uploaded_file

DB = "crm.db"
UPLOADS = Path("uploads")
UPLOADS.mkdir(exist_ok=True)

# Create a temp directory that will be automatically cleaned up
TEMP_DIR = tempfile.TemporaryDirectory()

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    app.secret_key = "dev"  # לא קריטי, רק לאפשר flash
    app.config['DB'] = DB
    
    # Register blueprints
    from api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from routes import clients
    app.register_blueprint(clients.bp)
    
    # Register reports blueprint
    from reports import client_report
    app.register_blueprint(client_report.bp_reports)
    
    from reports import reports_bp
    app.register_blueprint(reports_bp)
    
    return app

app = create_app()

# --- DB helpers -------------------------------------------------
def init_db():
    """Initialize core tables and indexes in the configured database.

    Uses the Flask app's DB config when available (tests, factory pattern),
    and falls back to the global DB path for legacy/standalone usage.
    """
    db_path = DB
    try:
        # When running inside an app context, prefer the configured DB path
        if current_app and current_app.config.get("DB"):
            db_path = current_app.config["DB"]
    except Exception:
        # Outside an app context current_app is not available – keep default DB
        pass

    with sqlite3.connect(db_path) as con:
        con.executescript(
            """
            create table if not exists client (
                id integer primary key,
                id_canon text unique,
                name text,
                first_name text,
                last_name text,
                phone text,
                email text,
                street text,
                house_number text,
                city text
            );
            create table if not exists client_details (
                client_id integer primary key references client(id) on delete cascade,
                first_name text,
                last_name text,
                date_of_birth date,
                email text,
                employer text,
                gender text,
                marital_status text,
                birth_country text,
                employer_address text,
                employer_phone text,
                employer_hp text
            );
            create table if not exists snapshot (
                id integer primary key,
                client_id integer,
                fund_code text,
                fund_number text,
                fund_type text,
                fund_name text,
                snapshot_date text,
                amount real check (amount > 0),
                source text,
                company text,
                is_active boolean DEFAULT 1,
                foreign key(client_id) references client(id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS snapshot_uq
            ON snapshot(client_id, fund_number, snapshot_date, source);
            CREATE INDEX IF NOT EXISTS idx_client_details_email
            ON client_details(email);
            CREATE INDEX IF NOT EXISTS idx_client_email 
            ON client(email);
            CREATE INDEX IF NOT EXISTS idx_client_phone 
            ON client(phone);
            CREATE INDEX IF NOT EXISTS idx_client_names 
            ON client(first_name, last_name);
            CREATE INDEX IF NOT EXISTS idx_snapshot_company 
            ON snapshot(company);
            create table if not exists client_notes (
                id integer primary key,
                client_id integer not null,
                note text not null,
                created_at text not null,
                foreign key(client_id) references client(id) on delete cascade
            );
            CREATE INDEX IF NOT EXISTS idx_client_notes_client_id
            ON client_notes(client_id);
            """
        )

        # Ensure new columns exist on existing databases (non-destructive)
        def ensure_column(table: str, column: str, col_type: str) -> None:
            cols = [c[1] for c in con.execute(f"PRAGMA table_info({table})")]
            if column not in cols:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

        # client extra contact fields
        ensure_column("client", "street", "text")
        ensure_column("client", "house_number", "text")
        ensure_column("client", "city", "text")

        # client_details extra personal/employment fields
        ensure_column("client_details", "gender", "text")
        ensure_column("client_details", "marital_status", "text")
        ensure_column("client_details", "birth_country", "text")
        ensure_column("client_details", "employer_address", "text")
        ensure_column("client_details", "employer_phone", "text")
        ensure_column("client_details", "employer_hp", "text")

        # client_notes reminder fields
        ensure_column("client_notes", "reminder_at", "text")
        ensure_column("client_notes", "dismissed_at", "text")

def get_latest_snapshot_month():
    """Return latest snapshot month in format YYYY-MM, or None if no data."""
    try:
        with sqlite3.connect(DB) as con:
            row = con.execute(
                "SELECT MAX(strftime('%Y-%m', snapshot_date)) FROM snapshot WHERE is_active = 1"
            ).fetchone()
            if row and row[0]:
                return row[0]
    except Exception:
        # In case snapshot table does not exist yet or other DB issues
        return None
    return None

def upsert_client_details(con, client_id: int, row: dict):
    """
    Upsert client_details - only fill missing fields, don't overwrite existing data
    
    Args:
        con: SQLite connection
        client_id: Client ID
        row: Row data with client_details fields
    """
    # Check if client_details already exists
    existing = con.execute(
        """
        SELECT 
            first_name, 
            last_name, 
            date_of_birth, 
            email, 
            employer,
            gender,
            marital_status,
            birth_country,
            employer_address,
            employer_phone,
            employer_hp
        FROM client_details 
        WHERE client_id = ?
        """,
        (client_id,),
    ).fetchone()
    
    if existing:
        # Update only NULL/empty fields
        (
            first_name,
            last_name,
            date_of_birth,
            email,
            employer,
            gender,
            marital_status,
            birth_country,
            employer_address,
            employer_phone,
            employer_hp,
        ) = existing
        
        updates = []
        params = []
        
        if not first_name and row.get("first_name"):
            updates.append("first_name = ?")
            params.append(row["first_name"])
        
        if not last_name and row.get("last_name"):
            updates.append("last_name = ?")
            params.append(row["last_name"])
        
        if not date_of_birth and row.get("date_of_birth"):
            updates.append("date_of_birth = ?")
            params.append(row["date_of_birth"])
        
        if not email and row.get("email"):
            updates.append("email = ?")
            params.append(row["email"])
        
        if not employer and row.get("employer"):
            updates.append("employer = ?")
            params.append(row["employer"])

        if not gender and row.get("gender"):
            updates.append("gender = ?")
            params.append(row["gender"])

        if not marital_status and row.get("marital_status"):
            updates.append("marital_status = ?")
            params.append(row["marital_status"])

        if not birth_country and row.get("birth_country"):
            updates.append("birth_country = ?")
            params.append(row["birth_country"])

        if not employer_address and row.get("employer_address"):
            updates.append("employer_address = ?")
            params.append(row["employer_address"])

        if not employer_phone and row.get("employer_phone"):
            updates.append("employer_phone = ?")
            params.append(row["employer_phone"])

        if not employer_hp and row.get("employer_hp"):
            updates.append("employer_hp = ?")
            params.append(row["employer_hp"])
        
        if updates:
            params.append(client_id)
            con.execute(
                f"UPDATE client_details SET {', '.join(updates)} WHERE client_id = ?",
                params
            )
    else:
        # Insert new client_details record
        con.execute(
            """INSERT INTO client_details 
               (client_id, first_name, last_name, date_of_birth, email, employer,
                gender, marital_status, birth_country, employer_address,
                employer_phone, employer_hp) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                client_id,
                row.get("first_name"),
                row.get("last_name"),
                row.get("date_of_birth"),
                row.get("email"),
                row.get("employer"),
                row.get("gender"),
                row.get("marital_status"),
                row.get("birth_country"),
                row.get("employer_address"),
                row.get("employer_phone"),
                row.get("employer_hp"),
            ),
        )

def insert_rows(df: pd.DataFrame, source: str, snap_date: str):
    from crm_ingestion.utils.normalize import normalize_id, normalize_name, create_client_key
    from datetime import datetime
    from crm_ingestion.utils.source_names import get_source_display_name
    
    # Normalize date to first of month for monthly snapshots
    if isinstance(snap_date, str):
        snap_date_obj = datetime.strptime(snap_date, '%Y-%m-%d')
    else:
        snap_date_obj = snap_date
    
    # Set to first day of month for monthly history
    normalized_date = snap_date_obj.replace(day=1).strftime('%Y-%m-%d')
    
    # Aggregate multiple tracks per fund for the same client within this upload.
    # This prevents "INSERT OR REPLACE" from overwriting rows when there are
    # several lines for the same fund_number in the same month and source, and
    # ensures snapshot holds the total balance per fund.
    if "id_canon" in df.columns and "fund_number" in df.columns:
        original_len = len(df)

        # Group only by the keys that correspond to the UNIQUE index
        # (client_id via id_canon, fund_number, snapshot_date, source).
        # For a single upload, snapshot_date and source are constant, so
        # grouping by (id_canon, fund_number) is sufficient.
        agg_dict = {"accumulated_amount": "sum"}

        # Keep representative values for descriptive columns, if they exist
        if "client_name" in df.columns:
            agg_dict["client_name"] = "first"
        if "fund_type" in df.columns:
            agg_dict["fund_type"] = "first"
        if "fund_code" in df.columns:
            agg_dict["fund_code"] = "first"
        if "fund_name" in df.columns:
            agg_dict["fund_name"] = "first"

        grouped = (
            df.groupby(["id_canon", "fund_number"], dropna=False)
            .agg(agg_dict)
            .reset_index()
        )

        # Ensure we have client_key for canonicalization; recompute from name + id
        grouped["client_key"] = grouped.apply(
            lambda row: create_client_key(row.get("client_name", ""), row["id_canon"]),
            axis=1,
        )

        df = grouped
        if original_len != len(df):
            print(
                f"Aggregated {original_len} raw rows into {len(df)} rows "
                f"by (id_canon, fund_number) before inserting into snapshot"
            )
    
    inserted_count = 0
    skipped_zero = 0
    skipped_duplicates = 0
    
    # Get company name from source code
    company = get_source_display_name(source)
    
    # Debug: Print summary of data to be inserted
    print(f"Preparing to insert {len(df)} rows from {source}")
    print(f"Unique clients in dataframe: {df['id_canon'].nunique()}")
    
    # Group by client to see how many funds each client has
    if 'fund_number' in df.columns:
        client_fund_counts = df.groupby('id_canon')['fund_number'].nunique()
        print(f"Top 5 clients by fund count:")
        for client_id, fund_count in client_fund_counts.nlargest(5).items():
            print(f"  Client {client_id}: {fund_count} funds")
    
    with sqlite3.connect(DB) as con:
        # טען כבר בהתחלה את כל ה‑client_key → client_id
        cur = con.execute("SELECT id, id_canon, name FROM client")
        key_map = {}
        id_canon_map = {}  # Map to track existing id_canon values
        for cid, id_canon, name in cur.fetchall():
            client_key = create_client_key(name, id_canon)
            key_map[client_key] = cid
            id_canon_map[id_canon] = cid
        
        # Process each row in the dataframe
        for _, row in df.iterrows():
            try:
                # Skip rows with zero or negative amounts
                if row["accumulated_amount"] <= 0:
                    skipped_zero += 1
                    continue
                
                # Use client_key for canonicalization
                client_key = row.get("client_key")
                if not client_key:
                    # Fallback if client_key not in row (shouldn't happen with updated loaders)
                    client_key = create_client_key(row["client_name"], row["id_canon"])
                
                # 1) bring/get client_id
                if client_key in key_map:
                    cid = key_map[client_key]
                else:
                    # Check if id_canon already exists (handle duplicates)
                    if row["id_canon"] in id_canon_map:
                        cid = id_canon_map[row["id_canon"]]
                        skipped_duplicates += 1
                    else:
                        try:
                            # Insert new client with basic data
                            cursor = con.execute(
                                "INSERT INTO client(id_canon, name, first_name, last_name, phone, email) VALUES(?,?,?,?,?,?)",
                                (
                                    row["id_canon"], 
                                    row["client_name"],
                                    "",  # first_name
                                    "",  # last_name
                                    "",  # phone
                                    ""   # email
                                )
                            )
                            cid = cursor.lastrowid
                            key_map[client_key] = cid
                            id_canon_map[row["id_canon"]] = cid
                        except sqlite3.IntegrityError as e:
                            # If insert fails due to duplicate id_canon, get the existing client_id
                            if 'UNIQUE constraint failed: client.id_canon' in str(e):
                                cursor = con.execute("SELECT id FROM client WHERE id_canon = ?", (row["id_canon"],))
                                result = cursor.fetchone()
                                if result:
                                    cid = result[0]
                                    id_canon_map[row["id_canon"]] = cid
                                    skipped_duplicates += 1
                                else:
                                    # This shouldn't happen, but log and skip if it does
                                    print(f"Error: Could not find client with id_canon {row['id_canon']} despite constraint failure")
                                    continue
                            else:
                                # Re-raise other integrity errors
                                raise
                
                # 1.5) Upsert client_details with empty values
                upsert_client_details(con, cid, {})
                
                # Get the fund_number for this row
                fund_number = row.get("fund_number", "")
                
                # 2) Insert or replace snapshot for monthly history
                try:
                    con.execute("""
                        INSERT OR REPLACE INTO snapshot (
                            client_id, fund_code, fund_number, fund_type, fund_name, 
                            snapshot_date, amount, source, company, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """, (
                        cid,
                        row.get("fund_code", ""),
                        fund_number,
                        row.get("fund_type", ""),
                        row.get("fund_name", ""),
                        normalized_date,
                        row["accumulated_amount"],
                        source,
                        company,
                    ))
                    inserted_count += 1
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e):
                        skipped_duplicates += 1
                    else:
                        print(f"Error processing row: {e}")
            except Exception as e:
                print(f"Error processing row: {e}")
        
        print(f"Inserted {inserted_count} records into the database")
        print(f"Skipped {skipped_duplicates} duplicates and {skipped_zero} rows with zero/negative amounts")
    con.commit()

# --- Routes -----------------------------------------------------
HTML_BASE = """
<!doctype html><title>Mini‑CRM</title>
<h1>{{ title }}</h1>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul style="color:red">{% for m in messages %}<li>{{ m }}</li>{% endfor %}</ul>
  {% endif %}
{% endwith %}
{{ body|safe }}
"""

@app.route("/")
def index():
    return redirect(url_for("clients"))

@app.route("/upload/", methods=["GET", "POST"])
def upload():
    """Modern upload page with wizard and preview functionality."""
    if request.method == "GET":
        return render_template("upload.html", now=date.today())
    
    # Handle file upload
    if "file" not in request.files:
        return jsonify({"error": "לא נבחר קובץ"}), 400
    
    file = request.files["file"]
    snap_date = request.form.get("snap_date")
    is_preview = request.form.get("preview") == "true"

    app.logger.info(
        "Upload request: filename=%s, snap_date=%s, preview=%s",
        file.filename,
        snap_date,
        is_preview,
    )
    
    if file.filename == "":
        return jsonify({"error": "לא נבחר קובץ"}), 400
    
    if not snap_date:
        return jsonify({"error": "חסר תאריך סנפשוט"}), 400
    
    try:
        # Save file to temp directory
        temp_path = Path(TEMP_DIR.name) / file.filename
        file.save(str(temp_path))
        
        # Load Excel file into DataFrame
        df_raw = pd.read_excel(str(temp_path), dtype=str)

        # Validate and transform using service helper
        df, file_type = transform_uploaded_file(df_raw, file.filename, snap_date)
        
        # If this is a preview request, return preview data
        if is_preview:
            unique_clients = df['client_key'].nunique() if 'client_key' in df.columns else 0
            preview_data = df.head(10).to_dict('records') if len(df) > 0 else []
            
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
            
            return jsonify({
                "file_type": file_type,
                "total_rows": len(df),
                "unique_clients": unique_clients,
                "preview": preview_data
            })
        
        # Insert into database
        insert_rows(df, file_type, snap_date)
        
        # Clean up temp file
        temp_path.unlink(missing_ok=True)
        
        return jsonify({
            "success": True,
            "message": f"הקובץ {file.filename} הועלה בהצלחה!",
            "rows_inserted": len(df),
            "file_type": file_type
        })
        
    except UploadProcessingError as e:
        # Validation/processing errors that should be shown to the user
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink(missing_ok=True)

        app.logger.warning("Upload failed for file %s: %s", file.filename, e.user_message)
        return jsonify({"error": e.user_message}), 400
    except Exception as e:
        # Clean up temp file on unexpected error
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink(missing_ok=True)

        app.logger.exception("Unexpected error during upload for file %s", file.filename)
        
        return jsonify({"error": f"שגיאה בעליית הקובץ: {str(e)}"}), 500

@app.route("/clients/")
def clients():
    """Modern clients page with DataTables."""
    default_month = get_latest_snapshot_month()
    return render_template("clients.html", now=date.today(), default_month=default_month)

@app.route("/client/<id_canon>")
def client_detail(id_canon):
    """Modern client detail page with cards, accordion, and sparklines."""
    with sqlite3.connect(DB) as con:
        # Get client info with all new fields
        client_row = con.execute(
            """
            SELECT 
                c.id,
                c.name,
                COALESCE(cd.first_name, c.first_name) AS first_name,
                COALESCE(cd.last_name, c.last_name) AS last_name,
                c.phone,
                COALESCE(cd.email, c.email) AS email,
                cd.date_of_birth,
                cd.employer,
                cd.gender,
                cd.marital_status,
                cd.birth_country,
                c.street,
                c.house_number,
                c.city,
                cd.employer_address,
                cd.employer_phone,
                cd.employer_hp
            FROM client c
            LEFT JOIN client_details cd ON c.id = cd.client_id
            WHERE c.id_canon = ?
            """,
            (id_canon,),
        ).fetchone()
        
        if not client_row:
            return "לקוח לא נמצא", 404
        
        (
            client_id,
            full_name,
            first_name_raw,
            last_name_raw,
            phone,
            email,
            date_of_birth,
            employer,
            gender,
            marital_status,
            birth_country,
            street,
            house_number,
            city,
            employer_address,
            employer_phone,
            employer_hp,
        ) = client_row

        full_name = full_name or ""
        first_name = first_name_raw or ""
        last_name = last_name_raw or ""

        # If no explicit first/last name, try to derive from full name
        if not first_name and not last_name and full_name:
            parts = full_name.split()
            if len(parts) == 1:
                first_name = parts[0]
            else:
                # Take first token as first name, rest as last name
                first_name = parts[0]
                last_name = " ".join(parts[1:])

        client = {
            "id": client_id,
            "name": full_name,
            "id_canon": id_canon,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone or "",
            "email": email or "",
            # Primary date field from client_details
            "date_of_birth": date_of_birth or "",
            # Alias for template field birth_date
            "birth_date": date_of_birth or "",
            # Personal details extras
            "gender": gender or "",
            "marital_status": marital_status or "",
            "birth_country": birth_country or "",
            # Contact details extras
            "street": street or "",
            "house_number": house_number or "",
            "city": city or "",
            # Primary employer field from client_details
            "employer": employer or "",
            # Aliases for template
            "employer_name": employer or "",
            "employer_address": employer_address or "",
            "employer_phone": employer_phone or "",
            "employer_hp": employer_hp or "",
        }
            
        # Get all funds for this client, aggregating all tracks per fund_number
        # at the latest snapshot date for that fund
        funds_data = con.execute(
            """
            WITH latest_funds AS (
                SELECT
                    s.fund_number,
                    MAX(s.snapshot_date) AS snapshot_date
                FROM snapshot s
                WHERE s.client_id = ? AND s.is_active = 1
                GROUP BY s.fund_number
            ),
            aggregated_funds AS (
                SELECT
                    COALESCE(s.fund_number, '') AS fund_number,
                    COALESCE(MIN(s.fund_type), 'לא זמין') AS fund_type,
                    COALESCE(MIN(s.fund_name), '') AS fund_name,
                    SUM(s.amount) AS amount,
                    MAX(s.snapshot_date) AS snapshot_date,
                    MIN(s.source) AS source
                FROM snapshot s
                JOIN latest_funds lf
                    ON lf.fund_number = s.fund_number
                    AND lf.snapshot_date = s.snapshot_date
                WHERE s.client_id = ? AND s.is_active = 1
                GROUP BY s.fund_number
            )
            SELECT
                fund_number,
                fund_type,
                fund_name,
                amount,
                snapshot_date,
                source
            FROM aggregated_funds
            ORDER BY fund_type, fund_number
            """, (client['id'], client['id'])
        ).fetchall()
    
    # Organize funds by type and create funds list
    funds_by_type = {}
    funds_list = []
    total_amount = 0
    sources = set()
    
    for i, fund_data in enumerate(funds_data):
        fund_number, fund_type, fund_name, amount, snapshot_date, source = fund_data
        
        fund = {
            'id': i + 1,  # Simple ID for JavaScript functions
            'fund_code': fund_number,
            'fund_number': fund_number,
            'fund_type': fund_type,
            'fund_name': fund_name,
            'amount': amount,
            'snapshot_date': snapshot_date,
            'source': source,
            'source_display': get_source_display_name(source)
        }
        
        # Add to both structures
        funds_list.append(fund)
        
        if fund_type not in funds_by_type:
            funds_by_type[fund_type] = []
        funds_by_type[fund_type].append(fund)
        
        total_amount += amount
        sources.add(source)
    
    # Add funds list to client object
    client['funds'] = funds_list
    fund_count = len(funds_data)
    
    return render_template(
        "client_detail.html",
        client=client,
        funds_by_type=funds_by_type,
        total_amount=total_amount,
        fund_count=fund_count,
        sources=list(sources),
        now=date.today()
    )

# Legacy dashboard route - kept for backward compatibility
# New API endpoints are now in api/routes.py

@app.route("/dashboard/")
def dashboard():
    default_month = get_latest_snapshot_month()
    return render_template("dashboard.html", now=date.today(), default_month=default_month)

# --- main -------------------------------------------------------
if __name__ == "__main__":
    init_db()
    # Make sure temp directory exists
    print(f"Using temporary directory: {TEMP_DIR.name}")
    app.run(debug=True)
    # Clean up temp directory when app exits
    TEMP_DIR.cleanup()
