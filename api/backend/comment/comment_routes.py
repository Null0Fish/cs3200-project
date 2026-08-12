from flask import Blueprint, jsonify, current_app
from backend.db_connection import get_db


# This blueprint handles routes useful for interacting with comments
comment = Blueprint("comment_routes", __name__)
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
        