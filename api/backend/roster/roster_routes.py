from flask import Blueprint, jsonify, current_app, redirect, url_for
from backend.db_connection import get_db


# This blueprint handles routes useful for interacting with rosters
rosters = Blueprint("roster_routes", __name__)
@rosters.route("/roster/<int:roster_id>", methods=["GET"])
def get_roster(roster_id: int):
    current_app.logger.info("GET /roster/<roster_id> handler")
    cursor = get_db().cursor(dictionary=True)
    
    if not isinstance(roster_id, int):
        return jsonify({{"error"} : {"ERROR cannot accept non-integer roster ID"}}), 403
    
    # cursor.execute(query, params)
    try:
        query = """
            SELECT 
            roster.roster_id, 
            roster.user_id, 
            roster.sport_id, 
            roster.division, 
            roster.start_date, 
            roster.end_date, 
            roster.gender, 
            roster.team_name,
            opening.required_gpa,
            opening.required_height_cm,
            opening.position,
            opening.grad_year,
            opening.opening_number,
            sport.name
            FROM roster
            LEFT OUTER JOIN opening ON opening.roster_id = roster.roster_id
            LEFT OUTER JOIN sport ON sport.sport_id = roster.sport_id
            WHERE roster.roster_id = %s;
        """
        cursor.execute(query, (roster_id,))
        opening_rows = cursor.fetchall()
        if not opening_rows:
            return jsonify({"error" : "A roster with that ID was not found!"}), 404

        response : dict[str, str | dict | list] = {}
        
        top = opening_rows[0]
        response['roster_id'] = top['roster_id']
        response['recruiter_id'] = top['user_id']
        response['sport_id'] = top['sport_id']
        response['division'] = top['division']
        response['roster_id'] = top['roster_id']
        response['start_date'] = top['start_date']
        response['end_date'] = top['end_date']
        response['gender'] = top['gender']
        response['team_name'] = top['team_name']
        response['sport_name'] = top['name']
        
        
        opening_list: list[dict[str, str]] = []
        for opening in opening_rows:
            if opening['opening_number'] is None:
                break
            formatted_opening: dict[str, str] = {}
            formatted_opening['opening_number'] = opening['opening_number']
            formatted_opening['required_gpa'] = opening['required_gpa']
            formatted_opening['required_height_cm'] = opening['required_height_cm']
            formatted_opening['position'] = opening['position']
            formatted_opening['grad_year'] = opening['grad_year']
            opening_list.append(formatted_opening)
            
        response['openings'] = opening_list
        
        return jsonify(response), 200
    except Exception as e:
        current_app.logger.error(f'Database error in get_roster: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()



