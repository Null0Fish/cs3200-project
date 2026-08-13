from flask import Flask
from dotenv import load_dotenv
import os
import logging

from backend.db_connection import init_app as init_db
from backend.simple.simple_routes import simple_routes
from backend.athletes.athlete_routes import athletes
from backend.clips.clip_routes import clips, clip_files
from backend.clips.clip_storage import MAX_CLIP_BYTES
from backend.recruiting.recruiting_routes import recruiting
from backend.engagement.engagement_routes import engagement
from backend.admin.admin_routes import admin
from backend.analytics.analytics_routes import analytics
from backend.assets.asset_routes import assets


def create_app():
    app = Flask(__name__)

    app.logger.setLevel(logging.DEBUG)
    app.logger.info('API startup')

    # Load environment variables from the .env file so they are
    # accessible via os.getenv() below.
    load_dotenv()

    # Secret key used by Flask for securely signing session cookies.
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Cap on any request body, which in practice means clip video uploads.
    # Flask rejects anything larger with a 413 before it reaches a route, so a
    # huge upload never gets written to disk.
    app.config["MAX_CONTENT_LENGTH"] = MAX_CLIP_BYTES

    # Database connection settings — values come from the .env file.
    app.config["MYSQL_DATABASE_USER"] = os.getenv("DB_USER").strip()
    app.config["MYSQL_DATABASE_PASSWORD"] = os.getenv("MYSQL_ROOT_PASSWORD").strip()
    app.config["MYSQL_DATABASE_HOST"] = os.getenv("DB_HOST").strip()
    app.config["MYSQL_DATABASE_PORT"] = int(os.getenv("DB_PORT").strip())
    app.config["MYSQL_DATABASE_DB"] = os.getenv("DB_NAME").strip()

    # Register the cleanup hook for the database connection.
    app.logger.info("create_app(): initializing database connection")
    init_db(app)

    # Register the routes from each Blueprint with the app object.
    #
    # Every TalentScout blueprint is mounted under /talent_scout, and each one
    # owns a group of related tables:
    #   athletes   - athlete profiles, personal records, events
    #   clips      - highlight clips and their comments
    #   recruiting - recruiters, universities, sports, rosters, openings
    #   engagement - who viewed which athlete profile / roster
    #   admin      - announcements and account moderation
    #   analytics  - read-only aggregate and de-identified data for analysts
    #
    # simple_routes is the template's demo/health-check blueprint and stays at
    # the root (/, /data, /niceMessage, ...). clip_files also stays at the root
    # so clip videos are served from /clips/<clip_id>, short enough to use
    # directly as a <video> src.
    app.logger.info("create_app(): registering blueprints")
    app.register_blueprint(simple_routes)
    app.register_blueprint(clip_files)
    app.register_blueprint(athletes, url_prefix="/talent_scout")
    app.register_blueprint(clips, url_prefix="/talent_scout")
    app.register_blueprint(recruiting, url_prefix="/talent_scout")
    app.register_blueprint(engagement, url_prefix="/talent_scout")
    app.register_blueprint(admin, url_prefix="/talent_scout")
    app.register_blueprint(analytics, url_prefix="/talent_scout")
    return app
