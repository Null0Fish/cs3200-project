from flask import Blueprint, jsonify, current_app
from backend.db_connection import get_db
from mysql.connector import Error

sports = Blueprint("sports", __name__)

@sports.route("/sports", methods=["GET"])
def get_sports():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /talent_scout/sports")
        query = """
            SELECT sport_id, name
            FROM sport
            ORDER BY name
        """
        cursor.execute(query)
        sports_list = cursor.fetchall()
        return jsonify(sports_list), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_sports: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
