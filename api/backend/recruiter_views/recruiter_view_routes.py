from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

recruiter_views = Blueprint("recruiter_views", __name__)


@recruiter_views.route("/recruiter_view/<int:athlete_id>", methods=["GET"])
def get_recruiter_views(athlete_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"GET /talent_scout/recruiter_view/{athlete_id}")
        query = """
            SELECT rv.athlete_id, rv.recruiter_id, rv.view_time,
                   u.first_name, u.last_name, u.email, u.phone
            FROM recruiter_view rv
                JOIN user u ON rv.recruiter_id = u.user_id
            WHERE rv.athlete_id = %s
            ORDER BY rv.view_time DESC
        """
        cursor.execute(query, (athlete_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_recruiter_views: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@recruiter_views.route("/recruiter_view/<int:athlete_id>", methods=["POST"])
def create_recruiter_view(athlete_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}
        current_app.logger.info(f"POST /talent_scout/recruiter_view/{athlete_id}")

        recruiter_id = data.get("recruiter_id")
        if recruiter_id is None:
            return jsonify({"error": "Missing required field: recruiter_id"}), 400

        cursor.execute("SELECT user_id FROM recruiter WHERE user_id = %s", (recruiter_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User is not a recruiter"}), 400

        cursor.execute(
            """
            INSERT INTO recruiter_view (athlete_id, recruiter_id, view_time)
            VALUES (%s, %s, NOW())
            """,
            (athlete_id, recruiter_id),
        )
        get_db().commit()
        return jsonify({"message": "Recruiter view recorded successfully"}), 201
    except Error as e:
        current_app.logger.error(f"Database error in create_recruiter_view: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
