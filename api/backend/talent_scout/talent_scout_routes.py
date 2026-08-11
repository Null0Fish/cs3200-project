from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for TalentScout routes
talent_scout = Blueprint("talent_scout", __name__)

@talent_scout.route("/athlete", methods=["GET"])
def get_all_athlete_info():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/athlete')
        query = "SELECT * FROM athlete"
        
        cursor.execute(query)
        athlete_list = cursor.fetchall()
        
        current_app.logger.info(f'Retrieved {len(athlete_list)} athletes')
        return jsonify(athlete_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_athletes: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@talent_scout.route("/athlete", methods=["POST"])
def upload_athlete_info():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info('POST /talent_scout/athlete')
        
        query = """
            INSERT INTO athlete (graduation_year, dob, gender, height_cm, weight_kg, gpa, recruitment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["graduation_year"],
            data["dob"],
            data["gender"],
            data["height_cm"],
            data["weight_kg"],
            data["gpa"],
            data["recruitment_status"]
        ))
        
        
        get_db().commit()
        return jsonify({"message": "Athlete created successfully", "athlete_id": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()