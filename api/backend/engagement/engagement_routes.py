"""
Engagement blueprint: who is looking at whom.

recruiter_view records a recruiter opening an athlete's profile (1.5, 2.6) and
roster_view records an athlete opening a recruiter's roster (2.5). Both tables
answer the same kind of question from opposite directions, so they are grouped
together here rather than split across two blueprints.

Both tables use a composite primary key with no timestamp in it, so a repeat
visit updates view_time instead of inserting a second row.

Registered in rest_entry.py with:
    app.register_blueprint(engagement, url_prefix='/talent_scout')
"""
from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

engagement = Blueprint("engagement", __name__)


# ---------------------------------------------------------------------------
# Recruiters viewing athletes
# ---------------------------------------------------------------------------

# Get every recruiter-view event, newest first (2.6)
# Optional filters: recruiter_id (the athletes this coach has looked at),
# athlete_id (same as the route below, without the path parameter).
# Example: /talent_scout/recruiter_view?recruiter_id=2
@engagement.route("/recruiter_view", methods=["GET"])
def get_all_recruiter_views():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/recruiter_view')
        query = """
            SELECT rv.athlete_id, rv.recruiter_id, rv.view_time,
                   athlete_user.first_name AS athlete_first_name,
                   athlete_user.last_name AS athlete_last_name,
                   recruiter_user.first_name AS recruiter_first_name,
                   recruiter_user.last_name AS recruiter_last_name
            FROM recruiter_view rv
                JOIN user athlete_user ON athlete_user.user_id = rv.athlete_id
                JOIN user recruiter_user ON recruiter_user.user_id = rv.recruiter_id
            WHERE 1=1
        """
        params = []
        for param, column in (("recruiter_id", "rv.recruiter_id"),
                              ("athlete_id", "rv.athlete_id")):
            value = request.args.get(param)
            if value:
                query += f" AND {column} = %s"
                params.append(value)
        query += " ORDER BY rv.view_time DESC"
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_recruiter_views: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get the coaches who have viewed one athlete's profile (1.5)
# Contact details come back with each row so the athlete can follow up.
# Example: /talent_scout/recruiter_view/1
@engagement.route("/recruiter_view/<int:athlete_id>", methods=["GET"])
def get_recruiter_views(athlete_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /talent_scout/recruiter_view/{athlete_id}')
        cursor.execute("""
            SELECT rv.athlete_id, rv.recruiter_id, rv.view_time,
                   u.first_name, u.last_name, u.email, u.phone,
                   uni.name AS university_name
            FROM recruiter_view rv
                JOIN user u ON u.user_id = rv.recruiter_id
                JOIN recruiter r ON r.user_id = rv.recruiter_id
                JOIN university uni ON uni.university_id = r.university_id
            WHERE rv.athlete_id = %s
            ORDER BY rv.view_time DESC
        """, (athlete_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_recruiter_views: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Record that a recruiter viewed an athlete's profile (1.5)
# Required field: recruiter_id.
# Example: POST /talent_scout/recruiter_view/1 with JSON body
@engagement.route("/recruiter_view/<int:athlete_id>", methods=["POST"])
def create_recruiter_view(athlete_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}
        current_app.logger.info(f'POST /talent_scout/recruiter_view/{athlete_id}')

        recruiter_id = data.get("recruiter_id")
        if recruiter_id is None:
            return jsonify({"error": "Missing required field: recruiter_id"}), 400

        cursor.execute("SELECT user_id FROM recruiter WHERE user_id = %s", (recruiter_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User is not a recruiter"}), 400

        cursor.execute("SELECT user_id FROM athlete WHERE user_id = %s", (athlete_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Athlete not found"}), 404

        cursor.execute("""
            INSERT INTO recruiter_view (athlete_id, recruiter_id, view_time)
            VALUES (%s, %s, NOW())
            ON DUPLICATE KEY UPDATE view_time = NOW()
        """, (athlete_id, recruiter_id))
        get_db().commit()
        return jsonify({"message": "Recruiter view recorded successfully"}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_recruiter_view: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# Athletes viewing rosters
# ---------------------------------------------------------------------------

# Get every roster-view event, newest first (2.5)
# Optional filters: recruiter_id (interest across all of that coach's rosters),
# roster_id, athlete_id.
# Example: /talent_scout/roster_view?recruiter_id=2
@engagement.route("/roster_view", methods=["GET"])
def get_all_roster_views():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/roster_view')
        query = """
            SELECT rv.user_id AS athlete_id, rv.roster_id, rv.view_time,
                   u.first_name, u.last_name, r.team_name,
                   r.user_id AS recruiter_id
            FROM roster_view rv
                JOIN user u ON u.user_id = rv.user_id
                JOIN roster r ON r.roster_id = rv.roster_id
            WHERE 1=1
        """
        params = []
        for param, column in (("recruiter_id", "r.user_id"),
                              ("roster_id", "rv.roster_id"),
                              ("athlete_id", "rv.user_id")):
            value = request.args.get(param)
            if value:
                query += f" AND {column} = %s"
                params.append(value)
        query += " ORDER BY rv.view_time DESC"
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_roster_views: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get the athletes who have viewed one roster (2.5)
# The recruiter profile page counts these rows to show interest per roster.
# Example: /talent_scout/roster_view/1
@engagement.route("/roster_view/<int:roster_id>", methods=["GET"])
def get_roster_views(roster_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /talent_scout/roster_view/{roster_id}')
        cursor.execute("""
            SELECT rv.user_id AS athlete_id, rv.roster_id, rv.view_time,
                   u.first_name, u.last_name, u.email, u.phone,
                   a.gpa, a.height_cm, a.graduation_year, a.recruitment_status
            FROM roster_view rv
                JOIN user u ON u.user_id = rv.user_id
                JOIN athlete a ON a.user_id = rv.user_id
            WHERE rv.roster_id = %s
            ORDER BY rv.view_time DESC
        """, (roster_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_roster_views: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Record that an athlete viewed a roster (2.5)
# Required field: user_id (the athlete).
# Example: POST /talent_scout/roster_view/1 with JSON body
@engagement.route("/roster_view/<int:roster_id>", methods=["POST"])
def create_roster_view(roster_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}
        current_app.logger.info(f'POST /talent_scout/roster_view/{roster_id}')

        user_id = data.get("user_id")
        if user_id is None:
            return jsonify({"error": "Missing required field: user_id"}), 400

        cursor.execute("SELECT user_id FROM athlete WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User is not an athlete"}), 400

        cursor.execute("SELECT roster_id FROM roster WHERE roster_id = %s", (roster_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Roster not found"}), 404

        cursor.execute("""
            INSERT INTO roster_view (user_id, roster_id, view_time)
            VALUES (%s, %s, NOW())
            ON DUPLICATE KEY UPDATE view_time = NOW()
        """, (user_id, roster_id))
        get_db().commit()
        return jsonify({"message": "Roster view recorded successfully"}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_roster_view: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
