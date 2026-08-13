"""
Admin blueprint: the platform administrator's tools.

Announcements are written only by administrators (announcement.user_id is a
foreign key to administrator), and the /user routes are the account-moderation
side of the same persona, so both live here.

Registered in rest_entry.py with:
    app.register_blueprint(admin, url_prefix='/talent_scout')
"""
from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

admin = Blueprint("admin", __name__)


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------

# Get all platform announcements (3.6)
# active=true returns only announcements whose scheduled window contains right now
# Example: /talent_scout/announcement?active=true
@admin.route("/announcement", methods=["GET"])
def get_announcements():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/announcement')
        active = request.args.get("active")
        # WHERE 1=1 lets us append AND clauses cleanly without special-casing the first filter
        query = """
            SELECT a.announcement_id, a.title, a.body, a.scheduled_start,
                   a.scheduled_end, u.first_name, u.last_name
            FROM announcement a
                LEFT JOIN user u ON a.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        if active and active.lower() == "true":
            query += " AND NOW() BETWEEN a.scheduled_start AND a.scheduled_end"
        query += " ORDER BY a.scheduled_start DESC"
        cursor.execute(query, params)
        announcement_list = cursor.fetchall()
        current_app.logger.info(f'Retrieved {len(announcement_list)} announcements')
        return jsonify(announcement_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_announcements: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get a single announcement, including which administrator posted it (3.6)
# Example: /talent_scout/announcement/1
@admin.route("/announcement/<int:announcement_id>", methods=["GET"])
def get_announcement(announcement_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /talent_scout/announcement/{announcement_id}')
        query = """
            SELECT a.announcement_id, a.title, a.body, a.scheduled_start,
                   a.scheduled_end, a.user_id, u.first_name, u.last_name
            FROM announcement a
                LEFT JOIN user u ON a.user_id = u.user_id
            WHERE a.announcement_id = %s
        """
        cursor.execute(query, (announcement_id,))
        announcement = cursor.fetchone()
        if not announcement:
            return jsonify({"error": "Announcement not found"}), 404
        return jsonify(announcement), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_announcement: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a new announcement (3.6)
# Required fields: user_id, title, scheduled_start, scheduled_end
# announcement.user_id is a foreign key to administrator, so the user_id supplied
# must already exist in the administrator table or the insert is rejected.
# Example: POST /talent_scout/announcement with JSON body
@admin.route("/announcement", methods=["POST"])
def create_announcement():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info('POST /talent_scout/announcement')
        required_fields = ["user_id", "title", "scheduled_start", "scheduled_end"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        query = """
            INSERT INTO announcement (user_id, title, body,
                                      scheduled_start, scheduled_end)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["user_id"],
            data["title"],
            data.get("body"),
            data["scheduled_start"],
            data["scheduled_end"],
        ))
        get_db().commit()
        return jsonify({"message": "Announcement created successfully", "announcement_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_announcement: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Edit an existing announcement (3.6 - admin fixes wording or reschedules)
# Can update any field except announcement_id and user_id
# Example: PUT /talent_scout/announcement/1 with JSON body containing fields to update
@admin.route("/announcement/<int:announcement_id>", methods=["PUT"])
def update_announcement(announcement_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info(f'PUT /talent_scout/announcement/{announcement_id}')
        cursor.execute("SELECT announcement_id FROM announcement WHERE announcement_id = %s",
                       (announcement_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Announcement not found"}), 404
        # Build update query dynamically based on provided fields
        allowed_fields = ["title", "body", "scheduled_start", "scheduled_end"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
        params.append(announcement_id)
        query = f"UPDATE announcement SET {', '.join(update_fields)} WHERE announcement_id = %s"
        cursor.execute(query, params)
        get_db().commit()
        return jsonify({"message": "Announcement updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in update_announcement: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete an announcement (3.6 - admin pulls down a notice)
# Example: DELETE /talent_scout/announcement/2
@admin.route("/announcement/<int:announcement_id>", methods=["DELETE"])
def delete_announcement(announcement_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'DELETE /talent_scout/announcement/{announcement_id}')
        cursor.execute("SELECT announcement_id FROM announcement WHERE announcement_id = %s",
                       (announcement_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Announcement not found"}), 404
        cursor.execute("DELETE FROM announcement WHERE announcement_id = %s", (announcement_id,))
        get_db().commit()
        return jsonify({"message": "Announcement deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_announcement: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# Account moderation
# ---------------------------------------------------------------------------

# Get every account with the role it belongs to (3.3, 3.4)
# The subtype tables (athlete, recruiter, administrator, analyst) each hold a
# user_id, so the role is derived by LEFT JOINing all four and taking whichever
# one matched. Optional filter: role=athlete|recruiter|administrator|analyst.
# Example: /talent_scout/user?role=athlete
@admin.route("/user", methods=["GET"])
def get_users():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/user')
        query = """
            SELECT u.user_id, u.first_name, u.last_name, u.email, u.phone,
                   CASE
                       WHEN ath.user_id IS NOT NULL THEN 'athlete'
                       WHEN rec.user_id IS NOT NULL THEN 'recruiter'
                       WHEN adm.user_id IS NOT NULL THEN 'administrator'
                       WHEN ana.user_id IS NOT NULL THEN 'analyst'
                       ELSE 'unassigned'
                   END AS role
            FROM user u
                LEFT JOIN athlete ath ON ath.user_id = u.user_id
                LEFT JOIN recruiter rec ON rec.user_id = u.user_id
                LEFT JOIN administrator adm ON adm.user_id = u.user_id
                LEFT JOIN analyst ana ON ana.user_id = u.user_id
        """
        params = []
        role = request.args.get("role")
        if role:
            # Filter on the subtype table directly; the CASE alias is not
            # available to a WHERE clause in MySQL.
            role_tables = {
                "athlete": "ath",
                "recruiter": "rec",
                "administrator": "adm",
                "analyst": "ana",
            }
            if role not in role_tables:
                return jsonify({"error": f"Unknown role: {role}"}), 400
            query += f" WHERE {role_tables[role]}.user_id IS NOT NULL"
        query += " ORDER BY u.user_id"
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_users: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one account, with a count of the content attached to it (3.1, 3.3)
# The counts are what an admin looks at before deciding to delete an account.
# Example: /talent_scout/user/1
@admin.route("/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /talent_scout/user/{user_id}')
        cursor.execute("""
            SELECT u.user_id, u.first_name, u.last_name, u.email, u.phone
            FROM user u
            WHERE u.user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM clip WHERE user_id = %s) AS clip_count,
                (SELECT COUNT(*) FROM comment WHERE user_id = %s) AS comment_count,
                (SELECT COUNT(*) FROM roster WHERE user_id = %s) AS roster_count
        """, (user_id, user_id, user_id))
        user.update(cursor.fetchone())
        return jsonify(user), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_user: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete any account regardless of role (3.3, 3.4)
# Deleting the user row cascades to the subtype table and to that account's
# clips, comments, personal records, rosters and recorded views.
# Example: DELETE /talent_scout/user/9
@admin.route("/user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'DELETE /talent_scout/user/{user_id}')
        cursor.execute("SELECT user_id FROM user WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User not found"}), 404
        cursor.execute("DELETE FROM user WHERE user_id = %s", (user_id,))
        get_db().commit()
        return jsonify({"message": "User account deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_user: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
