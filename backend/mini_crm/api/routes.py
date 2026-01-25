import sqlite3
import datetime as dt
from flask import current_app, jsonify, request
from . import api_bp
from crm_ingestion.utils.source_names import get_source_display_name
from reports.monthly_change import get_monthly_totals, compute_month_over_month_changes

def get_db_path():
    """Get database path from app config or default."""
    return current_app.config.get("DB", "crm.db")

@api_bp.route("/summary")
def summary():
    """Return totals for current DB (fast single query block)."""
    # Optional month filter in format YYYY-MM
    month_param = request.args.get("month")

    with sqlite3.connect(get_db_path()) as con:
        cur = con.cursor()

        target_month = None
        if month_param:
            month_param = month_param.strip()
            # Basic format validation YYYY-MM
            if len(month_param) == 7 and month_param[4] == "-" and month_param[:4].isdigit() and month_param[5:].isdigit():
                target_month = month_param
        
        if not target_month:
            # Fallback to latest month in data
            latest_row = cur.execute(
                "SELECT MAX(strftime('%Y-%m', snapshot_date)) FROM snapshot WHERE is_active = 1"
            ).fetchone()
            target_month = latest_row[0] if latest_row else None

        if not target_month:
            total_assets = 0
            by_source = {}
            by_type = {}
        else:
            q_total = """
                SELECT SUM(amount)
                FROM snapshot
                WHERE is_active = 1
                  AND strftime('%Y-%m', snapshot_date) = ?
            """
            q_source = """
                SELECT source, SUM(amount)
                FROM snapshot
                WHERE is_active = 1
                  AND strftime('%Y-%m', snapshot_date) = ?
                GROUP BY source
            """
            q_type = """
                SELECT COALESCE(fund_type, 'לא זמין'), SUM(amount)
                FROM snapshot
                WHERE is_active = 1
                  AND strftime('%Y-%m', snapshot_date) = ?
                GROUP BY fund_type
            """

            total_result = cur.execute(q_total, (target_month,)).fetchone()
            total_assets = total_result[0] if total_result and total_result[0] is not None else 0

            by_source = dict(cur.execute(q_source, (target_month,)).fetchall())
            by_type = dict(cur.execute(q_type, (target_month,)).fetchall())

    return jsonify(
        total_assets=round(total_assets, 2),
        by_source=by_source,
        by_fund_type=by_type,
    )


@api_bp.route("/monthly_change")
def monthly_change():
    """Return month-over-month changes in total assets for all clients."""
    db_path = get_db_path()
    monthly_totals = get_monthly_totals(db_path)
    changes = compute_month_over_month_changes(monthly_totals)
    return jsonify(changes=changes)

@api_bp.route("/history")
def history():
    """?client_id=123 – monthly layers for line‑chart in client page."""
    cid = request.args.get("client_id", type=int)
    
    if cid == 0:
        # Special case: return total monthly history for all clients
        sql = """
          SELECT strftime('%Y-%m', snapshot_date) AS ym,
                 SUM(amount) 
          FROM snapshot
          GROUP BY ym
          ORDER BY ym
        """
        with sqlite3.connect(get_db_path()) as con:
            rows = con.execute(sql).fetchall()
    elif cid:
        # Return history for specific client
        sql = """
          SELECT strftime('%Y-%m', snapshot_date) AS ym,
                 SUM(amount) 
          FROM snapshot
          WHERE client_id=? 
          GROUP BY ym
          ORDER BY ym
        """
        with sqlite3.connect(get_db_path()) as con:
            rows = con.execute(sql, (cid,)).fetchall()
    else:
        return jsonify({"error": "client_id required"}), 400

    return jsonify(history=[{"month": ym, "amount": round(a, 2)} for ym, a in rows])

@api_bp.route("/fund_history")
def fund_history():
    """Return monthly history for a specific fund of a client.

    Expected query params:
    - client_id: integer
    - fund_number: string (snapshot.fund_number)
    """
    client_id = request.args.get("client_id", type=int)
    fund_number = request.args.get("fund_number", type=str)

    if not client_id or not fund_number:
        return jsonify({"error": "client_id and fund_number are required"}), 400

    with sqlite3.connect(get_db_path()) as con:
        rows = con.execute(
            """
            SELECT snapshot_date, amount, source
            FROM snapshot
            WHERE client_id = ?
              AND fund_number = ?
              AND is_active = 1
            ORDER BY snapshot_date
            """,
            (client_id, fund_number),
        ).fetchall()

    history = []
    prev_amount = None
    for snapshot_date, amount, source in rows:
        amount = amount or 0
        change = None
        if prev_amount is not None:
            change = amount - prev_amount
        history.append(
            {
                "date": snapshot_date,
                "amount": amount,
                "source": source or "",
                "change": change,
            }
        )
        prev_amount = amount

    return jsonify(history=history)

@api_bp.route("/clients")
def clients_json():
    """Return clients data for DataTables."""
    # Optional month filter in format YYYY-MM
    month_param = request.args.get("month")

    with sqlite3.connect(get_db_path()) as con:
        cur = con.cursor()

        target_month = None
        if month_param:
            month_param = month_param.strip()
            if len(month_param) == 7 and month_param[4] == "-" and month_param[:4].isdigit() and month_param[5:].isdigit():
                target_month = month_param

        if not target_month:
            latest_row = cur.execute(
                "SELECT MAX(strftime('%Y-%m', snapshot_date)) FROM snapshot WHERE is_active = 1"
            ).fetchone()
            target_month = latest_row[0] if latest_row else None

        if not target_month:
            rows = cur.execute(
                """
                SELECT 
                    c.id,
                    c.name,
                    c.id_canon,
                    0 AS total_amount,
                    NULL AS sources,
                    0 AS fund_count,
                    NULL AS last_update
                FROM client c
                ORDER BY c.name
                """
            ).fetchall()
        else:
            # Get clients with their total amounts and sources for the latest snapshot_date only
            rows = cur.execute(
                """
                SELECT 
                    c.id,
                    c.name,
                    c.id_canon,
                    COALESCE(SUM(s.amount), 0) AS total_amount,
                    GROUP_CONCAT(DISTINCT s.source) AS sources,
                    COUNT(DISTINCT s.fund_number) AS fund_count,
                    MAX(s.snapshot_date) AS last_update
                FROM client c
                LEFT JOIN snapshot s 
                  ON s.client_id = c.id 
                 AND s.is_active = 1
                 AND strftime('%Y-%m', s.snapshot_date) = ?
                GROUP BY c.id, c.name, c.id_canon
                ORDER BY c.name
                """,
                (target_month,),
            ).fetchall()
        
        clients_data = []
        for row in rows:
            client_id, name, id_canon, total_amount, sources, fund_count, last_update = row
            # Map source codes to Hebrew display names
            source_list = sources.split(',') if sources else []
            source_display_list = [get_source_display_name(src) for src in source_list]
            source_display = ", ".join(source_display_list) if source_display_list else "אין נתונים"
            
            clients_data.append({
                "id": client_id,
                "name": name,
                "id_canon": id_canon,
                "total_amount": round(total_amount, 2),
                "sources": source_display,  # Use Hebrew display names
                "raw_sources": sources or "אין נתונים",  # Keep original codes for reference
                "fund_count": fund_count,
                "last_update": last_update or "לא זמין",
                "details_url": f"/client/{id_canon}"
            })
    
    return jsonify(clients_data)


@api_bp.route("/reminders")
def global_reminders():
    """Return all active client note reminders due up to today across all clients."""
    today = dt.date.today().isoformat()

    with sqlite3.connect(get_db_path()) as con:
        rows = con.execute(
            """
            SELECT
                cn.id,
                cn.note,
                cn.created_at,
                cn.reminder_at,
                cn.dismissed_at,
                c.id_canon,
                c.name
            FROM client_notes cn
            JOIN client c ON cn.client_id = c.id
            WHERE cn.reminder_at IS NOT NULL
              AND (cn.dismissed_at IS NULL OR cn.dismissed_at = '')
              AND cn.reminder_at <= ?
            ORDER BY cn.reminder_at, cn.created_at DESC, cn.id DESC
            """,
            (today,),
        ).fetchall()

    reminders = []
    for (
        note_id,
        note,
        created_at,
        reminder_at,
        dismissed_at,
        id_canon,
        name,
    ) in rows:
        reminders.append(
            {
                "id": note_id,
                "note": note or "",
                "created_at": created_at,
                "reminder_at": reminder_at,
                "dismissed_at": dismissed_at,
                "id_canon": id_canon,
                "client_name": name or "",
                "client_url": f"/client/{id_canon}",
            }
        )

    return jsonify(reminders)


@api_bp.route("/client/<id_canon>/details", methods=["GET"])
def client_details_get(id_canon):
    """Get client details for a specific client."""
    with sqlite3.connect(get_db_path()) as con:
        # Join client and client_details so we can fall back to client table values
        row = con.execute(
            """
            SELECT 
                c.name,
                COALESCE(cd.first_name, c.first_name, '') AS first_name,
                COALESCE(cd.last_name, c.last_name, '') AS last_name,
                cd.date_of_birth,
                COALESCE(cd.email, c.email, '') AS email,
                cd.employer
            FROM client c
            LEFT JOIN client_details cd ON c.id = cd.client_id
            WHERE c.id_canon = ?
            """,
            (id_canon,),
        ).fetchone()

        if not row:
            return jsonify({"error": "Client not found"}), 404

        full_name, first_name, last_name, date_of_birth, email, employer = row

        # If both names are empty, try to derive from full client name
        if (not first_name) and (not last_name) and full_name:
            parts = full_name.split()
            if len(parts) == 1:
                first_name = parts[0]
            else:
                first_name = parts[0]
                last_name = " ".join(parts[1:])

        # Normalize date_of_birth for HTML input[type=date] (YYYY-MM-DD)
        if date_of_birth:
            try:
                # First try ISO format as-is
                parsed = dt.datetime.strptime(date_of_birth, "%Y-%m-%d")
                date_of_birth = parsed.strftime("%Y-%m-%d")
            except ValueError:
                try:
                    # Fallback for legacy DD/MM/YYYY values from Excel
                    parsed = dt.datetime.strptime(date_of_birth, "%d/%m/%Y")
                    date_of_birth = parsed.strftime("%Y-%m-%d")
                except ValueError:
                    # Leave as-is if parsing fails
                    pass
        return jsonify(
            {
                "first_name": first_name or "",
                "last_name": last_name or "",
                "date_of_birth": date_of_birth or "",
                "email": email or "",
                "employer": employer or "",
            }
        )

@api_bp.route("/client/<id_canon>/details", methods=["POST"])
def client_details_post(id_canon):
    """Update client details for a specific client."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        with sqlite3.connect(get_db_path()) as con:
            # Get client ID
            client_row = con.execute("SELECT id FROM client WHERE id_canon = ?", (id_canon,)).fetchone()
            if not client_row:
                return jsonify({"error": "Client not found"}), 404
            
            client_id = client_row[0]
            
            # Validate email if provided
            email = data.get("email", "").strip()
            if email:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    return jsonify({"error": "Invalid email format"}), 400
            
            # Validate date_of_birth if provided
            date_of_birth = data.get("date_of_birth", "").strip()
            if date_of_birth:
                try:
                    from dateutil.parser import parse
                    parsed_date = parse(date_of_birth)
                    date_of_birth = parsed_date.strftime('%Y-%m-%d')
                except:
                    return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
            # Check if client_details exists
            existing = con.execute(
                "SELECT client_id FROM client_details WHERE client_id = ?",
                (client_id,)
            ).fetchone()
            
            if existing:
                # Update existing record
                updates = []
                params = []
                
                for field in ["first_name", "last_name", "email", "employer"]:
                    if field in data:
                        updates.append(f"{field} = ?")
                        params.append(data[field].strip() if data[field] else None)
                
                if date_of_birth:
                    updates.append("date_of_birth = ?")
                    params.append(date_of_birth)
                elif "date_of_birth" in data and not data["date_of_birth"]:
                    updates.append("date_of_birth = ?")
                    params.append(None)
                
                if updates:
                    params.append(client_id)
                    con.execute(
                        f"UPDATE client_details SET {', '.join(updates)} WHERE client_id = ?",
                        params
                    )
            else:
                # Insert new record
                con.execute(
                    """INSERT INTO client_details 
                       (client_id, first_name, last_name, date_of_birth, email, employer) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        client_id,
                        data.get("first_name", "").strip() or None,
                        data.get("last_name", "").strip() or None,
                        date_of_birth or None,
                        email or None,
                        data.get("employer", "").strip() or None
                    )
                )
            
            con.commit()
            logger.info(f"client_details updated id_canon={id_canon}")
            return jsonify({"status": "ok"})
            
    except Exception as e:
        logger.error(f"Error updating client details for {id_canon}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route("/client/<id_canon>/details", methods=["DELETE"])
def client_details_delete(id_canon):
    """Delete client details for a specific client."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with sqlite3.connect(get_db_path()) as con:
            # Get client ID
            client_row = con.execute("SELECT id FROM client WHERE id_canon = ?", (id_canon,)).fetchone()
            if not client_row:
                return jsonify({"error": "Client not found"}), 404
            
            client_id = client_row[0]
            
            # Delete client_details record
            con.execute("DELETE FROM client_details WHERE client_id = ?", (client_id,))
            con.commit()
            
            logger.info(f"client_details deleted id_canon={id_canon}")
            return jsonify({"status": "ok"})
            
    except Exception as e:
        logger.error(f"Error deleting client details for {id_canon}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/client/<id_canon>/notes", methods=["GET"])
def client_notes_get(id_canon):
    """Return all notes for a specific client ordered by created_at desc."""
    with sqlite3.connect(get_db_path()) as con:
        # Resolve client_id from id_canon
        row = con.execute("SELECT id FROM client WHERE id_canon = ?", (id_canon,)).fetchone()
        if not row:
            return jsonify({"error": "Client not found"}), 404

        client_id = row[0]

        notes = con.execute(
            """
            SELECT id, note, created_at, reminder_at, dismissed_at
            FROM client_notes
            WHERE client_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (client_id,),
        ).fetchall()

    return jsonify([
        {
            "id": nid,
            "note": note or "",
            "created_at": created_at,
            "reminder_at": reminder_at,
            "dismissed_at": dismissed_at,
        }
        for nid, note, created_at, reminder_at, dismissed_at in notes
    ])


@api_bp.route("/client/<id_canon>/notes", methods=["POST"])
def client_notes_post(id_canon):
    """Add a new note for a specific client.

    The payload must contain a non-empty "note" field. Each note is stored
    together with its creation timestamp (ISO string).
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        data = request.get_json(force=True)
        if not data or "note" not in data:
            return jsonify({"error": "Missing note field"}), 400

        note_text = (data.get("note") or "").strip()
        if not note_text:
            return jsonify({"error": "Note text cannot be empty"}), 400

        # Optional reminder date for popping the note later (YYYY-MM-DD)
        raw_reminder = (data.get("reminder_at") or "").strip()
        reminder_at = None
        if raw_reminder:
            try:
                parsed = dt.datetime.strptime(raw_reminder, "%Y-%m-%d")
                reminder_at = parsed.strftime("%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid reminder date format. Use YYYY-MM-DD"}), 400

        created_at = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(get_db_path()) as con:
            row = con.execute("SELECT id FROM client WHERE id_canon = ?", (id_canon,)).fetchone()
            if not row:
                return jsonify({"error": "Client not found"}), 404

            client_id = row[0]

            cursor = con.execute(
                """
                INSERT INTO client_notes (client_id, note, created_at, reminder_at, dismissed_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (client_id, note_text, created_at, reminder_at, None),
            )
            con.commit()

        logger.info("client_note added id_canon=%s note_id=%s", id_canon, cursor.lastrowid)
        return jsonify(
            {
                "status": "ok",
                "id": cursor.lastrowid,
                "note": note_text,
                "created_at": created_at,
                "reminder_at": reminder_at,
            }
        )

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("Error adding note for %s: %s", id_canon, e)
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/client/<id_canon>/notes/<int:note_id>/dismiss", methods=["POST"])
def client_notes_dismiss(id_canon, note_id):
    """Mark a specific note as dismissed for this client.

    This is used to stop popping reminders once the user has seen them.
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        with sqlite3.connect(get_db_path()) as con:
            # Resolve client_id from id_canon
            row = con.execute(
                "SELECT id FROM client WHERE id_canon = ?",
                (id_canon,),
            ).fetchone()
            if not row:
                return jsonify({"error": "Client not found"}), 404

            client_id = row[0]
            dismissed_at = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            cur = con.execute(
                """
                UPDATE client_notes
                SET dismissed_at = ?
                WHERE id = ? AND client_id = ?
                """,
                (dismissed_at, note_id, client_id),
            )
            con.commit()

            if cur.rowcount == 0:
                return jsonify({"error": "Note not found"}), 404

        logger.info("client_note dismissed id_canon=%s note_id=%s", id_canon, note_id)
        return jsonify({"status": "ok", "dismissed_at": dismissed_at})

    except Exception as e:
        logger.error("Error dismissing note for %s: %s", id_canon, e)
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/client/<id_canon>/notes/<int:note_id>/clear_reminder", methods=["POST"])
def client_notes_clear_reminder(id_canon, note_id):
    """Clear reminder fields for a specific note while keeping the note itself."""
    import logging

    logger = logging.getLogger(__name__)

    try:
        with sqlite3.connect(get_db_path()) as con:
            # Resolve client_id from id_canon
            row = con.execute(
                "SELECT id FROM client WHERE id_canon = ?",
                (id_canon,),
            ).fetchone()
            if not row:
                return jsonify({"error": "Client not found"}), 404

            client_id = row[0]

            cur = con.execute(
                """
                UPDATE client_notes
                SET reminder_at = NULL,
                    dismissed_at = NULL
                WHERE id = ? AND client_id = ?
                """,
                (note_id, client_id),
            )
            con.commit()

            if cur.rowcount == 0:
                return jsonify({"error": "Note not found"}), 404

        logger.info("client_note reminder cleared id_canon=%s note_id=%s", id_canon, note_id)
        return jsonify({"status": "ok"})

    except Exception as e:
        logger.error("Error clearing reminder for %s: %s", id_canon, e)
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/client/<id_canon>/notes/<int:note_id>/delete", methods=["POST"])
def client_notes_delete(id_canon, note_id):
    """Delete a specific note (and any reminder) for this client."""
    import logging

    logger = logging.getLogger(__name__)

    try:
        with sqlite3.connect(get_db_path()) as con:
            # Resolve client_id from id_canon
            row = con.execute(
                "SELECT id FROM client WHERE id_canon = ?",
                (id_canon,),
            ).fetchone()
            if not row:
                return jsonify({"error": "Client not found"}), 404

            client_id = row[0]

            cur = con.execute(
                "DELETE FROM client_notes WHERE id = ? AND client_id = ?",
                (note_id, client_id),
            )
            con.commit()

            if cur.rowcount == 0:
                return jsonify({"error": "Note not found"}), 404

        logger.info("client_note deleted id_canon=%s note_id=%s", id_canon, note_id)
        return jsonify({"status": "ok"})

    except Exception as e:
        logger.error("Error deleting note for %s: %s", id_canon, e)
        return jsonify({"error": "Internal server error"}), 500
