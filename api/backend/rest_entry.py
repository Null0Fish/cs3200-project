from flask import Flask
from dotenv import load_dotenv
import os
import logging

from backend.db_connection import init_app as init_db
from backend.simple.simple_routes import simple_routes
from backend.athletes.athlete_routes import athletes
from backend.clips.clip_routes import clips
from backend.announcements.announcement_routes import announcements
from backend.roster.roster_routes import rosters as roster_detail_routes
from backend.recruiter.recruiter_routes import recruiter
from backend.comment.comment_routes import comment
from backend.personal_record.personal_record_routes import personal_record
from backend.rosters.roster_routes import rosters
from backend.recruiter_views.recruiter_view_routes import recruiter_views
from backend.roster_views.roster_view_routes import roster_views
from backend.opening.opening_routes import openings



def create_app():
    app = Flask(__name__)

    app.logger.setLevel(logging.DEBUG)
    app.logger.info('API startup')

    # Load environment variables from the .env file so they are
    # accessible via os.getenv() below.
    load_dotenv()

    # Secret key used by Flask for securely signing session cookies.
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Database connection settings — values come from the .env file.
    app.config["MYSQL_DATABASE_USER"] = os.getenv("DB_USER").strip()
    app.config["MYSQL_DATABASE_PASSWORD"] = os.getenv("MYSQL_ROOT_PASSWORD").strip()
    app.config["MYSQL_DATABASE_HOST"] = os.getenv("DB_HOST").strip()
    app.config["MYSQL_DATABASE_PORT"] = int(os.getenv("DB_PORT").strip())
    app.config["MYSQL_DATABASE_DB"] = os.getenv("DB_NAME").strip()

    # Register the cleanup hook for the database connection.
    app.logger.info("create_app(): initializing database connection")
    init_db(app)

    # Register the routes from each Blueprint with the app object
    # and give a url prefix to each.
    app.logger.info("create_app(): registering blueprints")
    app.register_blueprint(simple_routes)
    app.register_blueprint(athletes, url_prefix="/talent_scout")
    app.register_blueprint(clips, url_prefix="/talent_scout")
    app.register_blueprint(announcements, url_prefix="/talent_scout")
    app.register_blueprint(roster_detail_routes, url_prefix="/talent_scout")
    app.register_blueprint(rosters, url_prefix="/talent_scout")
    app.register_blueprint(recruiter, url_prefix="/talent_scout")
    app.register_blueprint(comment, url_prefix="/talent_scout")
    app.register_blueprint(personal_record, url_prefix="/talent_scout")
    app.register_blueprint(recruiter_views, url_prefix="/talent_scout")
    app.register_blueprint(roster_views, url_prefix="/talent_scout")
    app.register_blueprint(openings, url_prefix="/talent_scout")
    return app
