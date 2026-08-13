"""
Clips blueprint: the content side of the platform.

Covers highlight clips and the comments left on them — comments have no meaning
apart from the clip they belong to, so both resources live together here.

A clip's video file is not in the database: clip.clip_url holds the file's name
and the assets blueprint serves it from /assets/clips. Uploads arrive here as a
multipart `video` field and are written by clip_storage.py, which is also where
the naming rules live.

Registered in rest_entry.py with:
    app.register_blueprint(clips, url_prefix='/talent_scout')
"""
import datetime

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.clips.clip_storage import delete_clip_file, save_clip_file
from mysql.connector import Error

clips = Blueprint("clips", __name__)


# ---------------------------------------------------------------------------
# Clips
# ---------------------------------------------------------------------------

# Get the clip feed, optionally narrowed to one athlete
# Serves 2.1 (recruiter scrolls the feed) and 3.1 (admin's unfiltered moderation feed).
# clip_url is the clip's video file under /assets/clips, or NULL when no video
# was ever attached; comment_count is what the moderation feed shows next to a
# clip so an admin can spot the ones with a comment thread to review.
# Example: /talent_scout/clip?athlete_id=1
@clips.route("/clip", methods=["GET"])
def get_clips():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/clip')
        athlete_id = request.args.get("athlete_id")
        # WHERE 1=1 lets us append AND clauses cleanly without special-casing the first filter
        query = """
            SELECT c.clip_id, c.caption, c.clip_url, c.posted_at,
                   c.user_id AS athlete_id, u.first_name, u.last_name,
                   (SELECT COUNT(*) FROM comment cm
                    WHERE cm.clip_id = c.clip_id) AS comment_count
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
            SELECT c.clip_id, c.caption, c.clip_url, c.posted_at,
                   c.user_id AS athlete_id,
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
# Required fields: user_id, caption. posted_at defaults to today if omitted, and
# clip_url is optional - a clip with no video file attached is still a valid row.
# clip.user_id is a foreign key to athlete, so recruiters and admins cannot post.

# Send the video as a multipart form with the file under `video` and the text
# fields alongside it; a plain JSON body still works and creates a clip with
# whatever clip_url it carries (or none), which can be filled in later via
# PUT /clip/<id>/video.
# An uploaded file is only named once the row exists, because it is named after
# the clip_id the insert hands back — hence the second UPDATE.
# Example: POST /talent_scout/clip with files={'video': ...}, data={...}
@clips.route("/clip", methods=["POST"])
def upload_clip():
    cursor = get_db().cursor(dictionary=True)
    try:
        # A request carrying a file is multipart, so its text fields arrive in
        # request.form rather than as JSON.
        data = request.form if request.files else (request.get_json() or {})
        current_app.logger.info('POST /talent_scout/clip')
        required_fields = ["user_id", "caption"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        query = """
            INSERT INTO clip (user_id, posted_at, caption, clip_url)
            VALUES (%s, COALESCE(%s, CURDATE()), %s, %s)
        """
        cursor.execute(query, (
            data["user_id"],
            # A form field left blank comes through as "" rather than absent,
            # and COALESCE only falls back to CURDATE() on a real NULL.
            data.get("posted_at") or None,
            data["caption"],
            data.get("clip_url"),
        ))
        clip_id = cursor.lastrowid

        video = request.files.get("video")
        if video and video.filename:
            try:
                clip_url = save_clip_file(clip_id, video)
            except ValueError as e:
                # A clip whose video was rejected is a row nobody can watch, so
                # drop it rather than leave it in the feed as a dead entry.
                get_db().rollback()
                return jsonify({"error": str(e)}), 400
            cursor.execute("UPDATE clip SET clip_url = %s WHERE clip_id = %s",
                           (clip_url, clip_id))

        get_db().commit()
        return jsonify({"message": "Clip created successfully", "clip_id": clip_id}), 201
    except Error as e:
        current_app.logger.error(f'Database error in upload_clip: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Attach or replace the video on a clip that already exists (1.3)
# Lets an athlete swap in a better cut without losing the clip's comments, and
# gives the seeded clips a way to get a video at all. The new file's name goes
# into clip_url, so whatever the clip pointed at before is no longer referenced.
# Example: PUT /talent_scout/clip/1/video with files={'video': ...}
@clips.route("/clip/<int:clip_id>/video", methods=["PUT"])
def upload_clip_video(clip_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'PUT /talent_scout/clip/{clip_id}/video')
        cursor.execute("SELECT clip_url FROM clip WHERE clip_id = %s", (clip_id,))
        clip = cursor.fetchone()
        if not clip:
            return jsonify({"error": "Clip not found"}), 404

        video = request.files.get("video")
        if not video or not video.filename:
            return jsonify({"error": "video is a required file field"}), 400

        try:
            clip_url = save_clip_file(clip_id, video)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Re-uploading with a different extension would otherwise leave the old
        # file on disk with nothing pointing at it.
        if clip["clip_url"] != clip_url:
            delete_clip_file(clip["clip_url"])

        cursor.execute("UPDATE clip SET clip_url = %s WHERE clip_id = %s",
                       (clip_url, clip_id))
        get_db().commit()
        return jsonify({
            "message": "Clip video uploaded successfully",
            "clip_url": clip_url,
        }), 200
    except Error as e:
        current_app.logger.error(f'Database error in upload_clip_video: {e}')
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
        # Build update query dynamically based on provided fields.
        # Passing clip_url as null detaches the video without deleting the clip.
        allowed_fields = ["caption", "clip_url"]
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
        cursor.execute("SELECT clip_url FROM clip WHERE clip_id = %s", (clip_id,))
        clip = cursor.fetchone()
        if not clip:
            return jsonify({"error": "Clip not found"}), 404
        cursor.execute("DELETE FROM clip WHERE clip_id = %s", (clip_id,))
        get_db().commit()
        # The row is gone, so nothing would ever ask for the file again. Take
        # it with the row rather than leaving it orphaned on disk — clip_ids
        # are never reused, so a leftover upload is dead weight forever.
        delete_clip_file(clip["clip_url"])
        return jsonify({"message": "Clip deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_clip: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# Comments on clips
# ---------------------------------------------------------------------------

# Get every comment on the platform, newest first (3.5)
# This is the admin's moderation list: one request returns the whole platform's
# comments, so the feed page can group them by clip instead of asking for each
# clip's thread separately. Optional filters: clip_id, user_id.
# comment.user_id is ON DELETE SET NULL, so first_name/last_name come back NULL
# for a comment whose author has since been deleted.
# Example: /talent_scout/comment?clip_id=1
@clips.route("/comment", methods=["GET"])
def get_comments():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/comment')
        # WHERE 1=1 lets us append AND clauses cleanly without special-casing the first filter
        query = """
            SELECT cm.comment_id, cm.clip_id, cm.content, cm.posted_at,
                   cm.user_id, u.first_name, u.last_name,
                   c.caption AS clip_caption, c.user_id AS athlete_id
            FROM comment cm
                JOIN clip c ON c.clip_id = cm.clip_id
                LEFT JOIN user u ON u.user_id = cm.user_id
            WHERE 1=1
        """
        params = []
        for param, column in (("clip_id", "cm.clip_id"),
                              ("user_id", "cm.user_id")):
            value = request.args.get(param)
            if value:
                query += f" AND {column} = %s"
                params.append(value)
        query += " ORDER BY cm.posted_at DESC, cm.comment_id DESC"
        cursor.execute(query, params)
        comment_list = cursor.fetchall()
        current_app.logger.info(f'Retrieved {len(comment_list)} comments')
        return jsonify(comment_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_comments: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get just the comment thread for a clip, newest first (3.5 moderation view)
# GET /clip/<id> already embeds these; this route exists so the frontend can
# refresh a thread after posting without re-fetching the whole clip.
# Example: /talent_scout/clip/1/comment
@clips.route("/clip/<int:clip_id>/comment", methods=["GET"])
def get_clip_comments(clip_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /talent_scout/clip/{clip_id}/comment')
        cursor.execute("SELECT clip_id FROM clip WHERE clip_id = %s", (clip_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Clip not found"}), 404
        cursor.execute("""
            SELECT cm.comment_id, cm.content, cm.posted_at, cm.user_id,
                   u.first_name, u.last_name
            FROM comment cm
                LEFT JOIN user u ON cm.user_id = u.user_id
            WHERE cm.clip_id = %s
            ORDER BY cm.posted_at DESC
        """, (clip_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_clip_comments: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Post a new comment on a clip
# Required fields: clip_id, user_id, content. posted_at defaults to today.
# comment.user_id points at user (not athlete), so recruiters can comment too.
# Example: POST /talent_scout/comment with JSON body
@clips.route("/comment", methods=["POST"])
def create_comment():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}
        current_app.logger.info('POST /talent_scout/comment')
        for field in ("clip_id", "user_id", "content"):
            if field not in data:
                return jsonify({"error": f"{field} is a required field"}), 400

        content = data["content"]
        if not isinstance(content, str) or not content.strip():
            return jsonify({"error": "content must be a non-empty string"}), 400

        cursor.execute("SELECT clip_id FROM clip WHERE clip_id = %s", (data["clip_id"],))
        if not cursor.fetchone():
            return jsonify({"error": "not a valid clip_id"}), 400

        cursor.execute("SELECT user_id FROM user WHERE user_id = %s", (data["user_id"],))
        if not cursor.fetchone():
            return jsonify({"error": "not a valid user_id"}), 400

        cursor.execute("""
            INSERT INTO comment (clip_id, user_id, posted_at, content)
            VALUES (%s, %s, %s, %s)
        """, (
            data["clip_id"],
            data["user_id"],
            data.get("posted_at") or datetime.date.today(),
            content,
        ))
        get_db().commit()
        return jsonify({
            "message": "Comment created successfully",
            "comment_id": cursor.lastrowid,
        }), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_comment: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Edit an existing comment
# Only the comment body can be changed; the clip and author stay fixed.
# Example: PUT /talent_scout/comment/4 with JSON body {"content": "..."}
@clips.route("/comment/<int:comment_id>", methods=["PUT"])
def update_comment(comment_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}
        current_app.logger.info(f'PUT /talent_scout/comment/{comment_id}')
        if "content" not in data:
            return jsonify({"error": "content is a required field"}), 400

        content = data["content"]
        if not isinstance(content, str) or not content.strip():
            return jsonify({"error": "content must be a non-empty string"}), 400

        cursor.execute("SELECT comment_id FROM comment WHERE comment_id = %s", (comment_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Comment not found"}), 404

        cursor.execute("UPDATE comment SET content = %s WHERE comment_id = %s",
                       (content, comment_id))
        get_db().commit()
        return jsonify({"message": "Comment updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in update_comment: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a comment for inappropriate content (3.5)
# Example: DELETE /talent_scout/comment/1
@clips.route("/comment/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'DELETE /talent_scout/comment/{comment_id}')
        cursor.execute("SELECT comment_id FROM comment WHERE comment_id = %s", (comment_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Comment not found"}), 404
        cursor.execute("DELETE FROM comment WHERE comment_id = %s", (comment_id,))
        get_db().commit()
        return jsonify({"message": "Comment deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_comment: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
