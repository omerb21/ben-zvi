"""
Client management routes Blueprint.
"""
from flask import Blueprint, request, jsonify, current_app
import sqlite3
import logging

logger = logging.getLogger(__name__)


def get_db_path():
    """Get database path from app config or default."""
    return current_app.config.get("DB", "crm.db")


# Create Blueprint
bp = Blueprint('clients', __name__)

@bp.route('/client/<client_id>/update', methods=['POST'])
def update_client(client_id):
    """Update client information."""
    try:
        data = request.json
        
        # Connect to database
        with sqlite3.connect(get_db_path()) as con:
            # Update client record
            con.execute("""
                UPDATE client 
                SET first_name=?, last_name=?, phone=?, email=?, 
                    street=?, house_number=?, city=?
                WHERE id_canon=?
            """, (
                data.get('first_name', ''),
                data.get('last_name', ''),
                data.get('phone', ''),
                data.get('email', ''),
                data.get('street', ''),
                data.get('house_number', ''),
                data.get('city', ''),
                client_id
            ))
            
            # Check if update was successful
            if con.total_changes > 0:
                logger.info(f"Updated client {client_id} successfully")
                return jsonify({'ok': True, 'message': 'Client updated successfully'})
            else:
                logger.warning(f"No client found with id_canon: {client_id}")
                return jsonify({'ok': False, 'message': 'Client not found'}), 404
                
    except Exception as e:
        logger.error(f"Error updating client {client_id}: {str(e)}")
        return jsonify({'ok': False, 'message': 'Internal server error'}), 500


@bp.route('/client/<client_id>/delete', methods=['POST'])
def delete_client(client_id):
    """Delete a client and its client_details by id_canon.

    This does not touch snapshot rows; they will simply no longer be
    joined to any client and therefore לא יוצגו במסכים.
    """
    try:
        with sqlite3.connect(get_db_path()) as con:
            cur = con.cursor()

            # Find numeric client ID first
            row = cur.execute(
                "SELECT id FROM client WHERE id_canon = ?",
                (client_id,),
            ).fetchone()
            if not row:
                logger.warning(f"delete_client: client not found id_canon={client_id}")
                return jsonify({'ok': False, 'message': 'Client not found'}), 404

            numeric_id = row[0]

            # Delete related client_details explicitly (in addition to FK ON DELETE)
            cur.execute("DELETE FROM client_details WHERE client_id = ?", (numeric_id,))
            # Delete client
            cur.execute("DELETE FROM client WHERE id = ?", (numeric_id,))
            con.commit()

            logger.info(f"Deleted client id_canon={client_id} (id={numeric_id})")
            return jsonify({'ok': True, 'message': 'הלקוח נמחק בהצלחה'})

    except Exception as e:
        logger.error(f"Error deleting client {client_id}: {str(e)}")
        return jsonify({'ok': False, 'message': 'שגיאה במחיקת הלקוח'}), 500
