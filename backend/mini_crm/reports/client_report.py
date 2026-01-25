"""
Client Report Blueprint for generating CSV/Excel/PDF reports.
"""
from flask import Blueprint, request, Response, render_template, abort, current_app
import sqlite3
import pandas as pd
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create Blueprint
bp_reports = Blueprint('bp_reports', __name__)


def get_db_path():
    """Get database path from app config or default."""
    return current_app.config.get("DB", "crm.db")

def fetch_client_funds(client_id: int, month: str = None):
    """
    Fetch client funds data for reporting.
    
    Args:
        client_id: Client ID
        month: Optional month filter (YYYY-MM format)
    
    Returns:
        pandas.DataFrame with client fund data
    """
    with sqlite3.connect(get_db_path()) as con:
        # If month is provided, filter by it; otherwise get latest snapshot_date
        if month:
            month_filter = f"{month}-01"  # Convert YYYY-MM to YYYY-MM-01
            date_condition = "AND s.snapshot_date = ?"
            params = (client_id, month_filter)
        else:
            # Get the latest snapshot_date for this client
            latest_date_query = """
                SELECT MAX(s.snapshot_date) 
                FROM snapshot s 
                WHERE s.client_id = ? AND s.is_active = 1
            """
            latest_date = con.execute(latest_date_query, (client_id,)).fetchone()[0]
            if not latest_date:
                return pd.DataFrame()  # No data found
            
            date_condition = "AND s.snapshot_date = ?"
            params = (client_id, latest_date)
        
        query = """
            SELECT c.first_name, c.last_name, c.id_canon,
                   s.fund_number, s.fund_name, s.fund_type,
                   s.amount, s.company, s.source, s.snapshot_date
            FROM snapshot s
            JOIN client c ON c.id = s.client_id
            WHERE s.is_active = 1
              AND c.id = ?
              {}
            ORDER BY s.amount DESC
        """.format(date_condition)
        
        df = pd.read_sql_query(query, con, params=params)
        return df

def _client_data(client_id: int):
    """Get client basic data for report headers."""
    with sqlite3.connect(get_db_path()) as con:
        query = """
            SELECT id_canon, first_name, last_name, name, phone, email
            FROM client 
            WHERE id = ?
        """
        result = con.execute(query, (client_id,)).fetchone()
        if result:
            return {
                'id_canon': result[0],
                'first_name': result[1] or '',
                'last_name': result[2] or '',
                'name': result[3] or '',
                'phone': result[4] or '',
                'email': result[5] or ''
            }
        return {}

def _csv_headers(client_id: int, month: str = None):
    """Generate CSV response headers."""
    import urllib.parse
    client = _client_data(client_id)
    client_name = client.get('name', f'client_{client_id}')
    month_str = f"_{month}" if month else "_latest"
    filename = f"client_report_{client_name}{month_str}.csv"
    # URL encode the filename to handle Hebrew characters
    encoded_filename = urllib.parse.quote(filename.encode('utf-8'))
    
    return {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': f'attachment; filename*=UTF-8\'\'\'{encoded_filename}'
    }

def _xlsx_headers(client_id: int, month: str = None):
    """Generate Excel response headers."""
    import urllib.parse
    client = _client_data(client_id)
    client_name = client.get('name', f'client_{client_id}')
    month_str = f"_{month}" if month else "_latest"
    filename = f"client_report_{client_name}{month_str}.xlsx"
    # URL encode the filename to handle Hebrew characters
    encoded_filename = urllib.parse.quote(filename.encode('utf-8'))
    
    return {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': f'attachment; filename*=UTF-8\'\'\'{encoded_filename}'
    }

def _pdf_headers(client_id: int, month: str = None):
    """Generate PDF response headers."""
    import urllib.parse
    client = _client_data(client_id)
    client_name = client.get('name', f'client_{client_id}')
    month_str = f"_{month}" if month else "_latest"
    filename = f"client_report_{client_name}{month_str}.pdf"
    # URL encode the filename to handle Hebrew characters
    encoded_filename = urllib.parse.quote(filename.encode('utf-8'))
    
    return {
        'Content-Type': 'application/pdf',
        'Content-Disposition': f'attachment; filename*=UTF-8\'\'\'{encoded_filename}'
    }

def _add_summary_sheet(writer, df):
    """Add summary sheet to Excel workbook."""
    if df.empty:
        return
    
    # Create summary data
    summary_data = {
        'סיכום כללי': [
            'סך הכל יתרות',
            'מספר קופות',
            'תאריך דוח'
        ],
        'ערך': [
            f"₪{df['amount'].sum():,.2f}",
            len(df),
            datetime.now().strftime('%d/%m/%Y')
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name='סיכום', index=False)
    
    # Pivot by fund type
    if 'fund_type' in df.columns:
        fund_type_pivot = df.groupby('fund_type')['amount'].sum().reset_index()
        fund_type_pivot.columns = ['סוג מוצר', 'יתרה']
        fund_type_pivot.to_excel(writer, sheet_name='לפי סוג מוצר', index=False)
    
    # Pivot by source
    if 'company' in df.columns:
        company_pivot = df.groupby('company')['amount'].sum().reset_index()
        company_pivot.columns = ['חברה', 'יתרה']
        company_pivot.to_excel(writer, sheet_name='לפי חברה', index=False)

@bp_reports.route('/report/client/<int:client_id>', methods=['GET'])
@bp_reports.route('/report/client/<int:client_id>.<fmt>', methods=['GET'])
def client_report(client_id, fmt='csv'):
    """Generate client report in specified format."""
    try:
        # Get optional month parameter
        month = request.args.get('month')  # Expected format: YYYY-MM
        
        # Validate month format if provided
        if month:
            try:
                datetime.strptime(month, '%Y-%m')
            except ValueError:
                abort(400, 'Invalid month format. Use YYYY-MM.')
        
        # Fetch client data
        df = fetch_client_funds(client_id, month)
        
        if df.empty:
            abort(404, 'No data found for this client')
        
        # Rename columns to Hebrew for export and format dates for human readability
        df_export = df.copy()

        # Format snapshot_date column (if present) as DD/MM/YYYY for display
        if 'snapshot_date' in df_export.columns:
            try:
                df_export['snapshot_date'] = pd.to_datetime(
                    df_export['snapshot_date'], errors='coerce'
                ).dt.strftime('%d/%m/%Y')
            except Exception:
                # If parsing fails for some rows, leave original values as-is
                pass
        df_export.columns = [
            'שם פרטי', 'שם משפחה', 'ת"ז',
            'מס\' קופה', 'שם קופה', 'סוג מוצר',
            'יתרה', 'חברה', 'מקור', 'תאריך צילום'
        ]
        
        if fmt == 'csv':
            buf = io.StringIO()
            df_export.to_csv(buf, index=False, encoding='utf-8-sig')
            return Response(buf.getvalue(), headers=_csv_headers(client_id, month))
            
        elif fmt == 'xlsx':
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='קופות')
                _add_summary_sheet(writer, df)
            buf.seek(0)
            return Response(buf.getvalue(), headers=_xlsx_headers(client_id, month))
            
        elif fmt == 'pdf':
            # For PDF, we'll need to implement template rendering
            client = _client_data(client_id)
            now = datetime.now()
            html = render_template('report_client_pdf.html', 
                                 rows=df.to_dict(orient='records'), 
                                 client=client, 
                                 month=month,
                                 total_amount=df['amount'].sum(),
                                 current_date=now.strftime('%d/%m/%Y'),
                                 current_datetime=now.strftime('%d/%m/%Y %H:%M'))
            
            # Try PDF generation, fallback to HTML if not available
            try:
                import pdfkit
                pdf = pdfkit.from_string(html, False, options={'page-size': 'A4', 'encoding': 'UTF-8'})
                return Response(pdf, headers=_pdf_headers(client_id, month))
            except ImportError:
                logger.warning("pdfkit not available, returning HTML instead")
                # Return HTML with PDF-like styling
                return Response(html, mimetype='text/html; charset=utf-8')
            except Exception as e:
                logger.error(f"PDF generation error: {str(e)}")
                # Fallback to HTML
                return Response(html, mimetype='text/html; charset=utf-8')
                
        else:
            abort(400, 'Unsupported format. Use csv, xlsx, or pdf')
            
    except Exception as e:
        logger.error(f"Error generating client report: {str(e)}")
        abort(500, 'Internal server error')
