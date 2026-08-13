"""
Recruiting blueprint: the recruiter side of the platform.

A recruiter belongs to a university, owns rosters, and each roster advertises
openings for a sport. Those four tables are always read and written together,
so they share one blueprint instead of four near-empty ones.

Registered in rest_entry.py with:
    app.register_blueprint(recruiting, url_prefix='/talent_scout')
"""
from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

recruiting = Blueprint("recruiting", __name__)


# ---------------------------------------------------------------------------
# Recruiters and universities
# ---------------------------------------------------------------------------

# Get every recruiter with their university (1.4 - athletes browsing programs)
# Optional filter: university_id.
# Example: /talent_scout/recruiter?university_id=1
@recruiting.route("/recruiter", methods=["GET"])
def get_recruiters():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/recruiter')
        query = """
            SELECT r.user_id AS recruiter_id, u.first_name, u.last_name,
                   u.email, u.phone, uni.university_id, uni.name AS university_name,
                   uni.website_url
            FROM recruiter r
                JOIN user u ON u.user_id = r.user_id
                JOIN university uni ON uni.university_id = r.university_id
            WHERE 1=1
        """
        params = []
        university_id = request.args.get("university_id")
        if university_id:
            query += " AND r.university_id = %s"
            params.append(university_id)
        query += " ORDER BY uni.name, u.last_name"
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_recruiters: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one recruiter with their university and rosters nested inside (1.5)
# This is what the athlete sees after spotting a coach in their viewer list, and
# what the recruiter's own profile page loads.
# Example: /talent_scout/recruiter/2
@recruiting.route("/recruiter/<int:recruiter_id>", methods=["GET"])
def get_recruiter(recruiter_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /talent_scout/recruiter/{recruiter_id}')
        cursor.execute("""
            SELECT r.user_id, r.university_id, u.first_name, u.last_name,
                   u.email, u.phone
            FROM recruiter r
                JOIN user u ON u.user_id = r.user_id
            WHERE r.user_id = %s
        """, (recruiter_id,))
        recruiter_row = cursor.fetchone()
        if not recruiter_row:
            return jsonify({"error": "A recruiter with that ID was not found!"}), 404

        cursor.execute("""
            SELECT ro.roster_id, ro.sport_id, ro.gender, ro.division,
                   ro.team_name, ro.start_date, ro.end_date, s.name AS sport_name
            FROM roster ro
                JOIN sport s ON s.sport_id = ro.sport_id
            WHERE ro.user_id = %s
            ORDER BY ro.start_date DESC
        """, (recruiter_id,))
        recruiter_row["rosters"] = cursor.fetchall()

        cursor.execute("""
            SELECT university_id, name, website_url
            FROM university
            WHERE university_id = %s
        """, (recruiter_row["university_id"],))
        university = cursor.fetchone()

        # university_id is NOT NULL on recruiter with a RESTRICT foreign key, so a
        # missing row here means the data was tampered with outside the API.
        if not university:
            return jsonify({"error": "Recruiter is missing university information."}), 500

        recruiter_row.pop("university_id", None)
        recruiter_row["university"] = university
        return jsonify(recruiter_row), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_recruiter: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a recruiter account (3.4)
# Deletes the user row so the ON DELETE CASCADE chain also clears the recruiter
# row, their rosters, those rosters' openings, and every recorded view.
# Example: DELETE /talent_scout/recruiter/6
@recruiting.route("/recruiter/<int:recruiter_id>", methods=["DELETE"])
def delete_recruiter(recruiter_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'DELETE /talent_scout/recruiter/{recruiter_id}')
        cursor.execute("SELECT user_id FROM recruiter WHERE user_id = %s", (recruiter_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Not a valid recruiter ID."}), 404
        cursor.execute("DELETE FROM user WHERE user_id = %s", (recruiter_id,))
        get_db().commit()
        return jsonify({"message": "Recruiter account deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_recruiter: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get the university list, with how many recruiters each one has on the platform
# Example: /talent_scout/university
@recruiting.route("/university", methods=["GET"])
def get_universities():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/university')
        cursor.execute("""
            SELECT uni.university_id, uni.name, uni.website_url,
                   COUNT(r.user_id) AS recruiter_count
            FROM university uni
                LEFT JOIN recruiter r ON r.university_id = uni.university_id
            GROUP BY uni.university_id, uni.name, uni.website_url
            ORDER BY uni.name
        """)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_universities: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get the sport catalog so the frontend can populate a sport dropdown
# Example: /talent_scout/sports
@recruiting.route("/sports", methods=["GET"])
def get_sports():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/sports')
        cursor.execute("""
            SELECT sport_id, name
            FROM sport
            ORDER BY name
        """)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_sports: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# Rosters
# ---------------------------------------------------------------------------

# Get all rosters (1.4 - athletes see what programs are recruiting)
# Optional filters: recruiter_id, sport_id, division, gender.
# Example: /talent_scout/roster?sport_id=1&division=D1
@recruiting.route("/roster", methods=["GET"])
def get_rosters():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/roster')
        query = """
            SELECT r.roster_id, r.user_id AS recruiter_id, r.sport_id,
                   s.name AS sport_name, r.division, r.start_date, r.end_date,
                   r.gender, r.team_name
            FROM roster r
                JOIN sport s ON r.sport_id = s.sport_id
            WHERE 1=1
        """
        params = []
        for param, column in (
            ("recruiter_id", "r.user_id"),
            ("sport_id", "r.sport_id"),
            ("division", "r.division"),
            ("gender", "r.gender"),
        ):
            value = request.args.get(param)
            if value:
                query += f" AND {column} = %s"
                params.append(value)
        query += " ORDER BY r.start_date DESC"
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_rosters: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one roster with its openings nested inside (2.2)
# roster LEFT JOIN opening returns one row per opening, so the rows are folded
# into a single object here: roster fields at the top, openings in a list.
# Example: /talent_scout/roster/1
@recruiting.route("/roster/<int:roster_id>", methods=["GET"])
def get_roster(roster_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /talent_scout/roster/{roster_id}')
        cursor.execute("""
            SELECT r.roster_id, r.user_id AS recruiter_id, r.sport_id,
                   s.name AS sport_name, r.division, r.start_date, r.end_date,
                   r.gender, r.team_name,
                   o.opening_number, o.required_gpa, o.required_height_cm,
                   o.position, o.grad_year
            FROM roster r
                LEFT JOIN opening o ON o.roster_id = r.roster_id
                LEFT JOIN sport s ON s.sport_id = r.sport_id
            WHERE r.roster_id = %s
            ORDER BY o.opening_number
        """, (roster_id,))
        rows = cursor.fetchall()
        if not rows:
            return jsonify({"error": "A roster with that ID was not found!"}), 404

        roster_fields = ["roster_id", "recruiter_id", "sport_id", "sport_name",
                         "division", "start_date", "end_date", "gender", "team_name"]
        response = {field: rows[0][field] for field in roster_fields}

        opening_fields = ["opening_number", "required_gpa", "required_height_cm",
                          "position", "grad_year"]
        # opening_number is NULL only on the filler row a LEFT JOIN produces for
        # a roster with no openings at all.
        response["openings"] = [
            {field: row[field] for field in opening_fields}
            for row in rows if row["opening_number"] is not None
        ]
        return jsonify(response), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_roster: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a roster for a recruiter (2.2)
# Required fields: user_id, sport_id, start_date, end_date, gender, team_name
# roster.user_id is a foreign key to recruiter, so athletes cannot post rosters.
# Example: POST /talent_scout/roster with JSON body
@recruiting.route("/roster", methods=["POST"])
def create_roster():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}
        current_app.logger.info('POST /talent_scout/roster')
        required_fields = ["user_id", "sport_id", "start_date", "end_date",
                           "gender", "team_name"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        cursor.execute("""
            INSERT INTO roster (user_id, sport_id, division, start_date,
                                end_date, gender, team_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data["user_id"],
            data["sport_id"],
            data.get("division"),
            data["start_date"],
            data["end_date"],
            data["gender"],
            data["team_name"],
        ))
        roster_id = cursor.lastrowid
        get_db().commit()
        return jsonify({"message": "Roster created successfully", "roster_id": roster_id}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_roster: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a roster posting (3.4 - admin removes a false roster)
# Openings and recorded roster views cascade with it.
# Example: DELETE /talent_scout/roster/1
@recruiting.route("/roster/<int:roster_id>", methods=["DELETE"])
def delete_roster(roster_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'DELETE /talent_scout/roster/{roster_id}')
        cursor.execute("SELECT roster_id FROM roster WHERE roster_id = %s", (roster_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Roster not found"}), 404
        cursor.execute("DELETE FROM roster WHERE roster_id = %s", (roster_id,))
        get_db().commit()
        return jsonify({"message": "Roster deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_roster: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# Openings on a roster
# ---------------------------------------------------------------------------

# Get openings, joined to the roster and sport they belong to
# Optional filters: roster_id, position, grad_year, sport_id, recruiter_id, and
# athlete_id — which returns only the openings that athlete actually qualifies
# for (1.4). A NULL requirement counts as "no requirement", so it always matches.
# Example: /talent_scout/opening?athlete_id=1
@recruiting.route("/opening", methods=["GET"])
def get_openings():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/opening')
        query = """
            SELECT o.opening_number, o.roster_id, o.required_gpa,
                   o.required_height_cm, o.position, o.grad_year,
                   r.user_id AS recruiter_id, r.division, r.start_date,
                   r.end_date, r.gender, r.team_name, s.name AS sport_name
            FROM opening o
                JOIN roster r ON r.roster_id = o.roster_id
                LEFT JOIN sport s ON s.sport_id = r.sport_id
            WHERE 1=1
        """
        params = []
        for param, column in (
            ("roster_id", "o.roster_id"),
            ("position", "o.position"),
            ("grad_year", "o.grad_year"),
            ("sport_id", "r.sport_id"),
            ("recruiter_id", "r.user_id"),
        ):
            value = request.args.get(param)
            if value:
                query += f" AND {column} = %s"
                params.append(value)

        athlete_id = request.args.get("athlete_id")
        if athlete_id:
            query += """
                AND (o.required_gpa IS NULL
                     OR o.required_gpa <= (SELECT gpa FROM athlete WHERE user_id = %s))
                AND (o.required_height_cm IS NULL
                     OR o.required_height_cm <= (SELECT height_cm FROM athlete WHERE user_id = %s))
                AND (o.grad_year IS NULL
                     OR o.grad_year = (SELECT graduation_year FROM athlete WHERE user_id = %s))
            """
            params.extend([athlete_id, athlete_id, athlete_id])

        query += " ORDER BY o.roster_id, o.opening_number"
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_openings: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Add an opening to a roster (2.2)
# Required field: roster_id. Optional: required_gpa, required_height_cm,
# position, grad_year.
# opening_number is part of a composite primary key with roster_id and is not
# AUTO_INCREMENT, so the next number for this roster is computed here.
# Example: POST /talent_scout/opening with JSON body
@recruiting.route("/opening", methods=["POST"])
def create_opening():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}
        current_app.logger.info('POST /talent_scout/opening')
        if "roster_id" not in data:
            return jsonify({"error": "roster_id is a required field"}), 400

        cursor.execute("""
            SELECT r.roster_id, MAX(o.opening_number) AS last_number
            FROM roster r
                LEFT JOIN opening o ON o.roster_id = r.roster_id
            WHERE r.roster_id = %s
            GROUP BY r.roster_id
        """, (data["roster_id"],))
        roster_row = cursor.fetchone()
        if not roster_row:
            return jsonify({"error": "not a valid roster_id"}), 400

        opening_number = (roster_row["last_number"] or 0) + 1
        cursor.execute("""
            INSERT INTO opening (opening_number, roster_id, required_gpa,
                                 required_height_cm, position, grad_year)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            opening_number,
            data["roster_id"],
            data.get("required_gpa"),
            data.get("required_height_cm"),
            data.get("position"),
            data.get("grad_year"),
        ))
        get_db().commit()
        return jsonify({
            "message": "Opening created successfully",
            "opening_number": opening_number,
            "roster_id": data["roster_id"],
        }), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_opening: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a single opening once a recruiter has filled the spot
# Both key parts are in the URL because opening's primary key is composite.
# Example: DELETE /talent_scout/roster/1/opening/2
@recruiting.route("/roster/<int:roster_id>/opening/<int:opening_number>", methods=["DELETE"])
def delete_opening(roster_id, opening_number):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(
            f'DELETE /talent_scout/roster/{roster_id}/opening/{opening_number}')
        cursor.execute("""
            SELECT opening_number FROM opening
            WHERE roster_id = %s AND opening_number = %s
        """, (roster_id, opening_number))
        if not cursor.fetchone():
            return jsonify({"error": "Opening not found"}), 404
        cursor.execute("""
            DELETE FROM opening
            WHERE roster_id = %s AND opening_number = %s
        """, (roster_id, opening_number))
        get_db().commit()
        return jsonify({"message": "Opening deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_opening: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
