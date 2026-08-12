from flask import Blueprint, jsonify, current_app, request
from backend.db_connection import get_db


# This blueprint handles routes useful for interacting with rosters
openings = Blueprint("opening_routes", __name__)
@openings.route("/opening", methods=["GET"])
def get_openings():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /talent_scout/opening")
        query = """
            SELECT
                opening.opening_number,
                opening.roster_id,
                opening.required_gpa,
                opening.required_height_cm,
                opening.position,
                opening.grad_year,
                roster.user_id AS recruiter_id,
                roster.division,
                roster.start_date,
                roster.end_date,
                roster.gender,
                roster.team_name,
                sport.name AS sport_name
            FROM opening
            JOIN roster ON roster.roster_id = opening.roster_id
            LEFT OUTER JOIN sport ON sport.sport_id = roster.sport_id
        """

        # Optional filters supplied as query string parameters
        filters: list[str] = []
        params: list[str] = []
        for param, column in (
            ("roster_id", "opening.roster_id"),
            ("position", "opening.position"),
            ("grad_year", "opening.grad_year"),
            ("sport_id", "roster.sport_id"),
            ("recruiter_id", "roster.user_id"),
        ):
            value = request.args.get(param)
            if value is not None:
                filters.append(f"{column} = %s")
                params.append(value)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY opening.roster_id, opening.opening_number"

        cursor.execute(query, tuple(params))
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        current_app.logger.error(f"Database error in get_openings: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@openings.route("/opening", methods=["POST"])
def create_opening():
    current_app.logger.info("POST /opening/")
    cursor = get_db().cursor(dictionary=True)

    # cursor.execute(query, params)
    try:
        data = request.get_json()
        if "roster_id" not in data:
            return jsonify({"error" : "roster_id is a required field"}), 400
        query = """
            SELECT roster.roster_id, MAX(opening.opening_number) AS last_id
            FROM roster
            LEFT OUTER JOIN opening ON opening.roster_id = roster.roster_id
            WHERE roster.roster_id = %s
            GROUP BY roster.roster_id
        """
        cursor.execute(query, (data["roster_id"],))
        last_opening = cursor.fetchone()
        if not last_opening.get("roster_id"):
            return jsonify({"error" : "not a valid roster_id"}), 400
        
        last_row_id = last_opening["last_id"] + 1 if last_opening["last_id"] is not None else 1
        
        query = """
            INSERT INTO opening (opening_number, roster_id, required_gpa, required_height_cm, position, grad_year)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            last_row_id,
            data["roster_id"],
            data.get("required_gpa"),
            data.get("required_height_cm"),
            data.get("position"),
            data.get("grad_year")
        ))
        get_db().commit()
        return jsonify({"message": "Opening created successfully", "opening_id": last_row_id}), 201
    except Exception as e:
        current_app.logger.error(f'Database error in create_opening: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()



