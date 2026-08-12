from flask import Blueprint, jsonify, current_app
from backend.db_connection import get_db


# This blueprint handles routes useful for interacting with personal records
personal_record = Blueprint("pr_routes", __name__)
@personal_record.route("/personal_record/", methods=["GET"])
def get_recruiter():
    current_app.logger.info("GET /personal_record handler")
    cursor = get_db().cursor(dictionary=True)
    
    try:
        query = """
            SELECT 
                CAST(personal_record.time AS CHAR) AS time,
                personal_record.score,
                personal_record.event_id,
                event.name AS event_name
            FROM personal_record
            JOIN event ON event.event_id = personal_record.event_id
        """
        cursor.execute(query)
        
        prs = cursor.fetchall()
        return jsonify(prs), 200
    except Exception as e:
        current_app.logger.error(f'Database error in get_recruiter: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()