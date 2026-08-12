from flask import Blueprint, jsonify, current_app, redirect, url_for
from backend.db_connection import get_db


# This blueprint handles routes useful for interacting with rosters
recruiter = Blueprint("recruiter_routes", __name__)
@recruiter.route("/recruiter/<int:recruiter_id>", methods=["GET"])
def get_recruiter(recruiter_id: int):
    current_app.logger.info("GET /roster/<recruiter_id> handler")
    cursor = get_db().cursor(dictionary=True)
    
    if not isinstance(recruiter_id, int):
        return jsonify({{"error"} : {"ERROR cannot accept non-integer recruiter ID"}}), 403
    
    # cursor.execute(query, params)
    try:
        query = """
            SELECT 
                recruiter.university_id,
                recruiter.user_id,
                user.first_name,
                user.last_name,
                user.email,
                user.phone
            FROM recruiter
            JOIN user ON user.user_id = recruiter.user_id
            JOIN university ON university.university_id = recruiter.university_id
            WHERE recruiter.user_id = %s;
        """
        cursor.execute(query, (recruiter_id,))
        recruiter_row = cursor.fetchone()
        if not recruiter_row:
            return jsonify({"error" : "A recruiter with that ID was not found!"}), 404

        query = """
            SELECT
                roster.sport_id,
                roster.gender,
                roster.division,
                sport.sport_id,
                sport.name AS name
            FROM roster
            JOIN sport ON roster.sport_id = sport.sport_id
            WHERE roster.user_id = %s
        """
        cursor.execute(query, (recruiter_id,))
        rosters = cursor.fetchall()
        recruiter_row["rosters"] = rosters
            
        
        query = """
            SELECT
                university.name,
                university.website_url,
                university.university_id
            FROM university
            WHERE university.university_id = %s
        """
        cursor.execute(query, (recruiter_row['university_id'],))
        university = cursor.fetchone()
        if not university:
            return jsonify({"error": "There was an anomoly in the recruiter's university information. Please report this."}), 500
        
        recruiter_row.pop("university_id", None)
        recruiter_row["university"] = university
        
        
        return jsonify(recruiter_row), 200
    except Exception as e:
        current_app.logger.error(f'Database error in get_recruiter: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()



