from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

roster_views = Blueprint("roster_views", __name__)


@roster_views.route("/roster_view/<int:roster_id>", methods=["GET"])
def get_roster_views(roster_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"GET /talent_scout/roster_view/{roster_id}")
        query = """
            SELECT rv.user_id AS athlete_id, rv.roster_id, rv.view_time,
                   u.first_name, u.last_name, u.email, u.phone
            FROM roster_view rv
                JOIN user u ON rv.user_id = u.user_id
            WHERE rv.roster_id = %s
            ORDER BY rv.view_time DESC
        """
        cursor.execute(query, (roster_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Database error in get_roster_views: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@roster_views.route("/roster_view/<int:roster_id>", methods=["POST"])
def create_roster_view(roster_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}
        current_app.logger.info(f"POST /talent_scout/roster_view/{roster_id}")

        user_id = data.get("user_id")
        if user_id is None:
            return jsonify({"error": "Missing required field: user_id"}), 400

        cursor.execute("SELECT user_id FROM athlete WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User is not an athlete"}), 400

        cursor.execute(
            """
            INSERT INTO roster_view (user_id, roster_id, view_time)
            VALUES (%s, %s, NOW())
            """,
            (user_id, roster_id),
        )
        get_db().commit()
        return jsonify({"message": "Roster view recorded successfully"}), 201
    except Error as e:
        current_app.logger.error(f"Database error in create_roster_view: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
