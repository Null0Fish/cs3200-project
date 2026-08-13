"""
Analytics blueprint: the data analyst persona (user stories 4.1 - 4.6).

Every route here is read-only and returns aggregates or de-identified rows. No
route in this blueprint returns a name, email, phone number or clip, so the
analyst can work with the data without being able to identify an athlete.

MySQL returns TIME columns as timedeltas, which Flask cannot serialize, so
times are returned both as a CHAR cast (for display) and as a raw second count
(for charting).

Registered in rest_entry.py with:
    app.register_blueprint(analytics, url_prefix='/talent_scout')
"""
from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

analytics = Blueprint("analytics", __name__)

# Whitelist of groupings the analyst may ask for (4.1, 4.2). The value is the
# column to group on plus any joins that column needs. Interpolating anything
# outside this dict into the query would be a SQL injection hole.
#
# "sport" reaches sport through roster_view: an athlete has no sport column of
# their own, so the rosters an athlete has looked at are the best available
# proxy. An athlete who viewed rosters in two sports is counted under both.
GROUP_BY_OPTIONS = {
    "gender": ("a.gender", ""),
    "graduation_year": ("a.graduation_year", ""),
    "recruitment_status": ("a.recruitment_status", ""),
    "sport": (
        "s.name",
        """
            JOIN roster_view rv ON rv.user_id = a.user_id
            JOIN roster r ON r.roster_id = rv.roster_id
            JOIN sport s ON s.sport_id = r.sport_id
        """,
    ),
}


# Get aggregate athlete metrics, grouped however the analyst asks (4.1, 4.2, 4.6)
# group_by: gender (default), graduation_year, recruitment_status, or sport.
# Optional filters: gender, grad_year, min_gpa, sport_id (sport_id only applies
# to the sport grouping, since that is the only one joined to a sport).
# Example: /talent_scout/analytics/athlete_summary?group_by=sport
@analytics.route("/analytics/athlete_summary", methods=["GET"])
def get_athlete_summary():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/analytics/athlete_summary')
        group_by = request.args.get("group_by", "gender")
        if group_by not in GROUP_BY_OPTIONS:
            return jsonify({
                "error": f"group_by must be one of: {', '.join(GROUP_BY_OPTIONS)}"
            }), 400
        group_column, joins = GROUP_BY_OPTIONS[group_by]

        query = f"""
            SELECT {group_column} AS group_value,
                   COUNT(*) AS athlete_count,
                   ROUND(AVG(a.gpa), 2) AS avg_gpa,
                   ROUND(AVG(a.height_cm), 1) AS avg_height_cm,
                   ROUND(AVG(a.weight_kg), 1) AS avg_weight_kg,
                   MIN(a.gpa) AS min_gpa,
                   MAX(a.gpa) AS max_gpa
            FROM athlete a
            {joins}
            WHERE 1=1
        """
        params = []
        for param, column in (("gender", "a.gender"),
                              ("grad_year", "a.graduation_year")):
            value = request.args.get(param)
            if value:
                query += f" AND {column} = %s"
                params.append(value)
        min_gpa = request.args.get("min_gpa")
        if min_gpa:
            query += " AND a.gpa >= %s"
            params.append(min_gpa)
        sport_id = request.args.get("sport_id")
        if sport_id and group_by == "sport":
            query += " AND r.sport_id = %s"
            params.append(sport_id)

        query += f" GROUP BY {group_column} ORDER BY {group_column}"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        current_app.logger.info(f'Retrieved {len(rows)} summary groups by {group_by}')
        return jsonify({"group_by": group_by, "groups": rows}), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_athlete_summary: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get de-identified athlete rows, one per athlete (4.3, 4.4)
# No names or contact details, so these rows are safe to hand off or export to
# CSV. Optional filters: gender, grad_year, min_gpa, max_gpa, status.
# Example: /talent_scout/analytics/athlete?gender=F&min_gpa=3.0
@analytics.route("/analytics/athlete", methods=["GET"])
def get_anonymous_athletes():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/analytics/athlete')
        query = """
            SELECT a.user_id AS anonymous_id, a.gender, a.gpa, a.height_cm,
                   a.weight_kg, a.graduation_year, a.recruitment_status,
                   TIMESTAMPDIFF(YEAR, a.dob, CURDATE()) AS age,
                   (SELECT COUNT(*) FROM clip c WHERE c.user_id = a.user_id) AS clip_count,
                   (SELECT COUNT(*) FROM personal_record pr
                    WHERE pr.user_id = a.user_id) AS record_count
            FROM athlete a
            WHERE 1=1
        """
        params = []
        for param, column, operator in (
            ("gender", "a.gender", "="),
            ("grad_year", "a.graduation_year", "="),
            ("status", "a.recruitment_status", "="),
            ("min_gpa", "a.gpa", ">="),
            ("max_gpa", "a.gpa", "<="),
        ):
            value = request.args.get(param)
            if value:
                query += f" AND {column} {operator} %s"
                params.append(value)
        query += " ORDER BY a.user_id"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        current_app.logger.info(f'Retrieved {len(rows)} anonymized athlete rows')
        return jsonify(rows), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_anonymous_athletes: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get performance over time, averaged per event per date (4.5)
# This is the series behind a "are times improving?" chart. Optional filters:
# event_id, start_date, end_date.
# Example: /talent_scout/analytics/personal_record?event_id=1
@analytics.route("/analytics/personal_record", methods=["GET"])
def get_personal_record_trend():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/analytics/personal_record')
        query = """
            SELECT e.event_id, e.name AS event_name, pr.date,
                   COUNT(*) AS record_count,
                   CAST(SEC_TO_TIME(AVG(TIME_TO_SEC(pr.time)
                        + MICROSECOND(pr.time) / 1000000)) AS CHAR) AS avg_time,
                   AVG(TIME_TO_SEC(pr.time)
                       + MICROSECOND(pr.time) / 1000000) AS avg_time_seconds,
                   ROUND(AVG(pr.score), 2) AS avg_score
            FROM personal_record pr
                JOIN event e ON e.event_id = pr.event_id
            WHERE 1=1
        """
        params = []
        for param, column, operator in (
            ("event_id", "pr.event_id", "="),
            ("start_date", "pr.date", ">="),
            ("end_date", "pr.date", "<="),
        ):
            value = request.args.get(param)
            if value:
                query += f" AND {column} {operator} %s"
                params.append(value)
        query += """
            GROUP BY e.event_id, e.name, pr.date
            ORDER BY e.name, pr.date
        """
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_personal_record_trend: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get one row per event with how much data backs it (4.1, 4.6)
# LEFT JOIN so events nobody has competed in still appear, with a count of 0 -
# an analyst needs to see where the data is thin.
# Example: /talent_scout/analytics/event
@analytics.route("/analytics/event", methods=["GET"])
def get_event_summary():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/analytics/event')
        cursor.execute("""
            SELECT e.event_id, e.name AS event_name,
                   COUNT(pr.user_id) AS record_count,
                   COUNT(DISTINCT pr.user_id) AS athlete_count,
                   CAST(MIN(pr.time) AS CHAR) AS best_time,
                   CAST(SEC_TO_TIME(AVG(TIME_TO_SEC(pr.time)
                        + MICROSECOND(pr.time) / 1000000)) AS CHAR) AS avg_time,
                   AVG(TIME_TO_SEC(pr.time)
                       + MICROSECOND(pr.time) / 1000000) AS avg_time_seconds,
                   MAX(pr.score) AS best_score
            FROM event e
                LEFT JOIN personal_record pr ON pr.event_id = e.event_id
            GROUP BY e.event_id, e.name
            ORDER BY e.name
        """)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_event_summary: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get platform-wide totals (4.1)
# One row of scalars for the top of the analyst dashboard. Each count is its own
# subquery because the tables are not joinable without fanning the counts out.
# Example: /talent_scout/analytics/platform_summary
@analytics.route("/analytics/platform_summary", methods=["GET"])
def get_platform_summary():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /talent_scout/analytics/platform_summary')
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM athlete) AS athlete_count,
                (SELECT COUNT(*) FROM recruiter) AS recruiter_count,
                (SELECT COUNT(*) FROM university) AS university_count,
                (SELECT COUNT(*) FROM clip) AS clip_count,
                (SELECT COUNT(*) FROM comment) AS comment_count,
                (SELECT COUNT(*) FROM roster) AS roster_count,
                (SELECT COUNT(*) FROM opening) AS opening_count,
                (SELECT COUNT(*) FROM personal_record) AS record_count,
                (SELECT ROUND(AVG(gpa), 2) FROM athlete) AS avg_gpa,
                (SELECT COUNT(*) FROM athlete
                 WHERE recruitment_status = 'open') AS open_to_recruitment_count,
                (SELECT COUNT(*) FROM athlete
                 WHERE recruitment_status = 'committed') AS committed_count
        """)
        return jsonify(cursor.fetchone()), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_platform_summary: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
