"""
Athlete blueprint: everything that hangs off an athlete's profile.

Covers the athlete table itself plus the athletic performance data that only
makes sense in the context of an athlete (personal records and the event
catalog they are recorded against).

Registered in rest_entry.py with:
    app.register_blueprint(athletes, url_prefix='/talent_scout')
"""
from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

athletes = Blueprint("athletes", __name__)


# ---------------------------------------------------------------------------
# Athlete profiles
# ---------------------------------------------------------------------------

# Get all athletes with optional filtering by academics and metrics (2.4)
# Recruiters use this to query for athletes that meet specific criteria.
# Example: /talent_scout/athlete?min_gpa=3.5&min_height_cm=170&grad_year=2029
@athletes.route("/athlete", methods=["GET"])
def get_all_athlete_info():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/athlete')
        # Query parameters are added after the main part of the URL.
        # Example: http://localhost:4000/talent_scout/athlete?min_gpa=3.00
        min_gpa = request.args.get("min_gpa")
        min_height_cm = request.args.get("min_height_cm")
        grad_year = request.args.get("grad_year")
        gender = request.args.get("gender")
        status = request.args.get("status")
        # WHERE 1=1 lets us append AND clauses cleanly without special-casing the first filter
        query = """
            SELECT a.user_id, u.first_name, u.last_name, a.gender, a.gpa,
                   a.height_cm, a.weight_kg, a.graduation_year,
                   a.recruitment_status
            FROM athlete a
                JOIN user u ON a.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        if min_gpa:
            query += " AND a.gpa >= %s"
            params.append(min_gpa)
        if min_height_cm:
            query += " AND a.height_cm >= %s"
            params.append(min_height_cm)
        if grad_year:
            query += " AND a.graduation_year = %s"
            params.append(grad_year)
        if gender:
            query += " AND a.gender = %s"
            params.append(gender)
        if status:
            query += " AND a.recruitment_status = %s"
            params.append(status)
        query += " ORDER BY a.gpa DESC"
        cursor.execute(query, params)
        athlete_list = cursor.fetchall()
        current_app.logger.info(f'Retrieved {len(athlete_list)} athletes')
        return jsonify(athlete_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_athlete_info: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get detailed information about a specific athlete including clips and personal records (2.3)
# time is CAST to CHAR because mysql-connector returns TIME as a timedelta,
# which Flask cannot serialize to JSON.
# Example: /talent_scout/athlete/1
@athletes.route("/athlete/<int:athlete_id>", methods=["GET"])
def get_athlete_detail(athlete_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /talent_scout/athlete/{athlete_id}')
        query = """
            SELECT a.user_id, u.first_name, u.last_name, u.email, u.phone,
                   a.dob, a.gender, a.gpa, a.height_cm, a.weight_kg,
                   a.graduation_year, a.recruitment_status
            FROM athlete a
                JOIN user u ON a.user_id = u.user_id
            WHERE a.user_id = %s
        """
        cursor.execute(query, (athlete_id,))
        athlete = cursor.fetchone()
        if not athlete:
            return jsonify({"error": "Athlete not found"}), 404
        # Reuse the same cursor for the follow-up queries
        cursor.execute("""
            SELECT clip_id, caption, posted_at
            FROM clip
            WHERE user_id = %s
            ORDER BY posted_at DESC
        """, (athlete_id,))
        athlete["clips"] = cursor.fetchall()
        cursor.execute("""
            SELECT e.name AS event, pr.date, CAST(pr.time AS CHAR) AS time, pr.score
            FROM personal_record pr
                JOIN event e ON pr.event_id = e.event_id
            WHERE pr.user_id = %s
            ORDER BY pr.date DESC
        """, (athlete_id,))
        athlete["personal_records"] = cursor.fetchall()
        return jsonify(athlete), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_athlete_detail: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create the athlete profile for an existing user (1.1)
# Required fields: user_id, graduation_year, dob, gender, height_cm, weight_kg, gpa
# athlete.user_id is the primary key AND a foreign key to user, and it is not
# AUTO_INCREMENT, so the user row must already exist and user_id must be supplied.
# cursor.lastrowid would return 0 for this table, so we echo back user_id instead.
# Example: POST /talent_scout/athlete with JSON body
@athletes.route("/athlete", methods=["POST"])
def upload_athlete_info():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info('POST /talent_scout/athlete')
        required_fields = ["user_id", "graduation_year", "dob", "gender",
                           "height_cm", "weight_kg", "gpa"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        query = """
            INSERT INTO athlete (user_id, graduation_year, dob, gender,
                                 height_cm, weight_kg, gpa, recruitment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["user_id"],
            data["graduation_year"],
            data["dob"],
            data["gender"],
            data["height_cm"],
            data["weight_kg"],
            data["gpa"],
            data.get("recruitment_status", "open"),
        ))
        get_db().commit()
        return jsonify({"message": "Athlete created successfully", "user_id": data["user_id"]}), 201
    except Error as e:
        current_app.logger.error(f'Database error in upload_athlete_info: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update an existing athlete's information (1.2 metrics, 1.6 recruitment status)
# Can update any field except user_id
# Example: PUT /talent_scout/athlete/1 with JSON body containing fields to update
@athletes.route("/athlete/<int:athlete_id>", methods=["PUT"])
def update_athlete_info(athlete_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info(f'PUT /talent_scout/athlete/{athlete_id}')
        cursor.execute("SELECT user_id FROM athlete WHERE user_id = %s", (athlete_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Athlete not found"}), 404
        # Build update query dynamically based on provided fields
        allowed_fields = ["graduation_year", "dob", "gender", "height_cm",
                          "weight_kg", "gpa", "recruitment_status"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
        params.append(athlete_id)
        query = f"UPDATE athlete SET {', '.join(update_fields)} WHERE user_id = %s"
        cursor.execute(query, params)
        get_db().commit()
        return jsonify({"message": "Athlete updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in update_athlete_info: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete an athlete account (3.3)
# Deletes the user row rather than just the athlete row: ON DELETE CASCADE then
# clears athlete, clip, comment, personal_record and both view tables. Deleting
# only from athlete would leave a user row belonging to no subtype.
# Example: DELETE /talent_scout/athlete/9
@athletes.route("/athlete/<int:athlete_id>", methods=["DELETE"])
def delete_athlete(athlete_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'DELETE /talent_scout/athlete/{athlete_id}')
        cursor.execute("SELECT user_id FROM athlete WHERE user_id = %s", (athlete_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Athlete not found"}), 404
        cursor.execute("DELETE FROM user WHERE user_id = %s", (athlete_id,))
        get_db().commit()
        return jsonify({"message": "Athlete account deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_athlete: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# Personal records and the event catalog
# ---------------------------------------------------------------------------

# Get every personal record on the platform, newest first (4.5)
# Optional filters: athlete_id, event_id.
# time is CAST to CHAR because mysql-connector returns TIME as a timedelta.
# Example: /talent_scout/personal_record?event_id=1
@athletes.route("/personal_record", methods=["GET"])
def get_personal_records():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/personal_record')
        query = """
            SELECT pr.user_id AS athlete_id, u.first_name, u.last_name,
                   pr.date, pr.event_id, e.name AS event_name,
                   CAST(pr.time AS CHAR) AS time, pr.score
            FROM personal_record pr
                JOIN event e ON e.event_id = pr.event_id
                JOIN user u ON u.user_id = pr.user_id
            WHERE 1=1
        """
        params = []
        athlete_id = request.args.get("athlete_id")
        event_id = request.args.get("event_id")
        if athlete_id:
            query += " AND pr.user_id = %s"
            params.append(athlete_id)
        if event_id:
            query += " AND pr.event_id = %s"
            params.append(event_id)
        query += " ORDER BY pr.date DESC"
        cursor.execute(query, params)
        records = cursor.fetchall()
        current_app.logger.info(f'Retrieved {len(records)} personal records')
        return jsonify(records), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_personal_records: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one athlete's personal record history (1.2, 4.5)
# Ordered oldest-first so the frontend can chart improvement over time.
# Example: /talent_scout/athlete/1/personal_record
@athletes.route("/athlete/<int:athlete_id>/personal_record", methods=["GET"])
def get_athlete_personal_records(athlete_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /talent_scout/athlete/{athlete_id}/personal_record')
        cursor.execute("SELECT user_id FROM athlete WHERE user_id = %s", (athlete_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Athlete not found"}), 404
        cursor.execute("""
            SELECT pr.date, pr.event_id, e.name AS event_name,
                   CAST(pr.time AS CHAR) AS time, pr.score
            FROM personal_record pr
                JOIN event e ON e.event_id = pr.event_id
            WHERE pr.user_id = %s
            ORDER BY pr.date
        """, (athlete_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_athlete_personal_records: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Record a new personal record for an athlete (1.1, 1.2)
# Required fields: event_id, date. Optional: time, score.
# The primary key is (user_id, date, event_id), so posting the same event twice
# on the same day is a duplicate and comes back as a 500 from MySQL.
# Example: POST /talent_scout/athlete/1/personal_record with JSON body
@athletes.route("/athlete/<int:athlete_id>/personal_record", methods=["POST"])
def create_athlete_personal_record(athlete_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}
        current_app.logger.info(f'POST /talent_scout/athlete/{athlete_id}/personal_record')
        for field in ["event_id", "date"]:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        cursor.execute("SELECT user_id FROM athlete WHERE user_id = %s", (athlete_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Athlete not found"}), 404
        cursor.execute("SELECT event_id FROM event WHERE event_id = %s", (data["event_id"],))
        if not cursor.fetchone():
            return jsonify({"error": "Not a valid event_id"}), 400
        cursor.execute("""
            INSERT INTO personal_record (user_id, date, event_id, time, score)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            athlete_id,
            data["date"],
            data["event_id"],
            data.get("time"),
            data.get("score"),
        ))
        get_db().commit()
        return jsonify({"message": "Personal record created successfully"}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_athlete_personal_record: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get the event catalog so the frontend can populate an event dropdown
# Example: /talent_scout/event
@athletes.route("/event", methods=["GET"])
def get_events():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/event')
        cursor.execute("""
            SELECT event_id, name
            FROM event
            ORDER BY name
        """)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_events: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
