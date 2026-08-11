from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error
# Create a Blueprint for clip routes
# Register in rest_entry.py with:
#   app.register_blueprint(clips, url_prefix='/talent_scout')
clips = Blueprint("clips", __name__)
# Get the clip feed, optionally narrowed to one athlete
# Serves 2.1 (recruiter scrolls the feed) and 3.1 (admin's unfiltered moderation feed).
# The video file itself is served from /clips/<clip_id>, so the frontend builds
# the <video src> from clip_id rather than from a stored URL.
# Example: /talent_scout/clip?athlete_id=1
@clips.route("/clip", methods=["GET"])
def get_clips():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/clip')
        athlete_id = request.args.get("athlete_id")
        # WHERE 1=1 lets us append AND clauses cleanly without special-casing the first filter
        query = """
            SELECT c.clip_id, c.caption, c.posted_at, c.user_id AS athlete_id,
                   u.first_name, u.last_name
            FROM clip c
                JOIN user u ON c.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        if athlete_id:
            query += " AND c.user_id = %s"
            params.append(athlete_id)
        query += " ORDER BY c.posted_at DESC"
        cursor.execute(query, params)
        clip_list = cursor.fetchall()
        current_app.logger.info(f'Retrieved {len(clip_list)} clips')
        return jsonify(clip_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_clips: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
# Get one clip with the posting athlete's details and its comments (2.3)
# This is the route behind "see more information about the athletes in clips he sees" -
# the recruiter taps a clip in the feed and gets the athlete's metrics back.
# Example: /talent_scout/clip/1
@clips.route("/clip/<int:clip_id>", methods=["GET"])
def get_clip(clip_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /talent_scout/clip/{clip_id}')
        query = """
            SELECT c.clip_id, c.caption, c.posted_at, c.user_id AS athlete_id,
                   u.first_name, u.last_name, a.gpa, a.height_cm, a.weight_kg,
                   a.graduation_year, a.recruitment_status
            FROM clip c
                JOIN athlete a ON c.user_id = a.user_id
                JOIN user u ON a.user_id = u.user_id
            WHERE c.clip_id = %s
        """
        cursor.execute(query, (clip_id,))
        clip = cursor.fetchone()
        if not clip:
            return jsonify({"error": "Clip not found"}), 404
        # Reuse the same cursor for the follow-up query
        cursor.execute("""
            SELECT cm.comment_id, cm.content, cm.posted_at,
                   u.first_name, u.last_name
            FROM comment cm
                LEFT JOIN user u ON cm.user_id = u.user_id
            WHERE cm.clip_id = %s
            ORDER BY cm.posted_at DESC
        """, (clip_id,))
        clip["comments"] = cursor.fetchall()
        return jsonify(clip), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_clip: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
# Upload a highlight clip (1.3)
# Required fields: user_id, caption. posted_at defaults to today if omitted.
# clip.user_id is a foreign key to athlete, so recruiters and admins cannot post.
# Returns clip_id because the video file then gets written to /clips/<clip_id>.
# Example: POST /talent_scout/clip with JSON body
@clips.route("/clip", methods=["POST"])
def upload_clip():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info('POST /talent_scout/clip')
        required_fields = ["user_id", "caption"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        query = """
            INSERT INTO clip (user_id, posted_at, caption)
            VALUES (%s, COALESCE(%s, CURDATE()), %s)
        """
        cursor.execute(query, (
            data["user_id"],
            data.get("posted_at"),
            data["caption"],
        ))
        get_db().commit()
        return jsonify({"message": "Clip created successfully", "clip_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f'Database error in upload_clip: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
# Edit a clip's caption (1.3 - the "edit" link under each clip in Wireframe 2)
# Only the caption is editable; user_id and clip_id are fixed.
# Example: PUT /talent_scout/clip/1 with JSON body containing caption
@clips.route("/clip/<int:clip_id>", methods=["PUT"])
def update_clip(clip_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info(f'PUT /talent_scout/clip/{clip_id}')
        cursor.execute("SELECT clip_id FROM clip WHERE clip_id = %s", (clip_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Clip not found"}), 404
        # Build update query dynamically based on provided fields
        allowed_fields = ["caption"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
        params.append(clip_id)
        query = f"UPDATE clip SET {', '.join(update_fields)} WHERE clip_id = %s"
        cursor.execute(query, params)
        get_db().commit()
        return jsonify({"message": "Clip updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in update_clip: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
# Delete a clip for a content violation (3.2). Comments on it cascade with it.
# Example: DELETE /talent_scout/clip/1
@clips.route("/clip/<int:clip_id>", methods=["DELETE"])
def delete_clip(clip_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'DELETE /talent_scout/clip/{clip_id}')
        cursor.execute("SELECT clip_id FROM clip WHERE clip_id = %s", (clip_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Clip not found"}), 404
        cursor.execute("DELETE FROM clip WHERE clip_id = %s", (clip_id,))
        get_db().commit()
        return jsonify({"message": "Clip deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_clip: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()