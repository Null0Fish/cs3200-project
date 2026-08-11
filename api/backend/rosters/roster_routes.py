from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

rosters = Blueprint("rosters", __name__)


@rosters.route("/roster", methods=["GET"])
def get_rosters():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /talent_scout/roster")
        query = """
            SELECT r.roster_id, r.user_id AS recruiter_id, r.sport_id,
                   s.name AS sport_name, r.division, r.start_date, r.end_date,
                   r.gender, r.team_name
            FROM roster r
                JOIN sport s ON r.sport_id = s.sport_id
            ORDER BY r.start_date DESC
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_rosters: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@rosters.route("/roster", methods=["POST"])
def create_roster():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}
        current_app.logger.info("POST /talent_scout/roster")

        required_fields = [
            "user_id",
            "sport_id",
            "start_date",
            "end_date",
            "gender",
            "team_name",
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        cursor.execute(
            """
            INSERT INTO roster (user_id, sport_id, division, start_date, end_date, gender, team_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data["user_id"],
                data["sport_id"],
                data.get("division"),
                data["start_date"],
                data["end_date"],
                data["gender"],
                data["team_name"],
            ),
        )
        roster_id = cursor.lastrowid
        get_db().commit()
        return jsonify({"message": "Roster created successfully", "roster_id": roster_id}), 201
    except Error as e:
        current_app.logger.error(f"Database error in create_roster: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
