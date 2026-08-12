import datetime

from flask import Blueprint, jsonify, current_app, request
from backend.db_connection import get_db


# This blueprint handles routes useful for interacting with comments
comment = Blueprint("comment_routes", __name__)
# Post a new comment on a clip
# Required fields: clip_id, user_id, content
# posted_at is optional and defaults to today
# Example: POST /talent_scout/comment with JSON body
@comment.route("/comment", methods=["POST"])
def create_comment():
    current_app.logger.info("POST /comment handler")
    cursor = get_db().cursor(dictionary=True)

    try:
        data = request.get_json()
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

        query = """
            INSERT INTO comment (clip_id, user_id, posted_at, content)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
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
    except Exception as e:
        current_app.logger.error(f'Database error in create_comment: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Edit an existing comment
# Only the comment body can be changed; the clip and author stay fixed
# Example: PUT /talent_scout/comment/4 with JSON body {"content": "..."}
@comment.route("/comment/<int:comment_id>", methods=["PUT"])
def update_comment(comment_id: int):
    current_app.logger.info(f"PUT /comment/{comment_id} handler")
    cursor = get_db().cursor(dictionary=True)

    if comment_id <= 0:
        return jsonify({"error": "ERROR cannot accept non-positive comment ID"}), 403

    try:
        data = request.get_json()
        if "content" not in data:
            return jsonify({"error": "content is a required field"}), 400

        content = data["content"]
        if not isinstance(content, str) or not content.strip():
            return jsonify({"error": "content must be a non-empty string"}), 400

        cursor.execute("SELECT comment_id FROM comment WHERE comment_id = %s", (comment_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Not a valid comment ID."}), 404

        query = """
            UPDATE comment
            SET content = %s
            WHERE comment_id = %s
        """
        cursor.execute(query, (content, comment_id))
        get_db().commit()
        return jsonify({"message": "Comment updated successfully"}), 200
    except Exception as e:
        current_app.logger.error(f'Database error in update_comment: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@comment.route("/comment/<int:comment_id>", methods=["DELETE"])
def delete_recruiter(comment_id: int):
    current_app.logger.info("DELETE /comment/<comment_id> handler")
    cursor = get_db().cursor(dictionary=True)
    
    if not isinstance(comment_id, int) or comment_id <= 0:
        return jsonify({"error" : "ERROR cannot accept non-integer comment ID"}), 403
    
    try:
        query = """
            SELECT comment.comment_id
            FROM comment
            WHERE comment.comment_id = %s
        """
        cursor.execute(query, (comment_id,))
        is_comment: bool = len(cursor.fetchall()) > 0
        if not is_comment:
            return jsonify({"error" : "Not a valid comment ID."}), 404       
        
        query = """
            DELETE FROM comment
            WHERE comment.comment_id = %s;
        """
        cursor.execute(query, (comment_id,))
        get_db().commit()
        return jsonify({}), 204
    except Exception as e:
        current_app.logger.error(f'Database error in delete_comment: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        