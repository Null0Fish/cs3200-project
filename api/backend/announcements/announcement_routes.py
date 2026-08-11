from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error
# Create a Blueprint for announcement routes
# Register in rest_entry.py with:
#   app.register_blueprint(announcements, url_prefix='/talent_scout')
announcements = Blueprint("announcements", __name__)
# Get all platform announcements (3.6)
# active=true returns only announcements whose scheduled window contains right now
# Example: /talent_scout/announcement?active=true
@announcements.route("/announcement", methods=["GET"])
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
@announcements.route("/announcement/<int:announcement_id>", methods=["GET"])
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
@announcements.route("/announcement", methods=["POST"])
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
@announcements.route("/announcement/<int:announcement_id>", methods=["PUT"])
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
@announcements.route("/announcement/<int:announcement_id>", methods=["DELETE"])
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