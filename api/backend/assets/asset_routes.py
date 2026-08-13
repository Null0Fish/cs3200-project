"""
Assets blueprint: static files the browser loads directly.

Highlight-clip video files live in api/assets/clips and are served from
/assets/clips/<filename>. A clip row stores its file name in clip.clip_url with
a leading slash, so the <video src> the frontend builds is this route's base URL
concatenated with clip_url.

Unlike every other blueprint this one is registered without the /talent_scout
prefix - these are files, not resources in the data model.

Registered in rest_entry.py with:
    app.register_blueprint(assets)
"""
import os
from pathlib import Path

from flask import Blueprint, current_app, send_from_directory

assets = Blueprint("assets", __name__)

# Absolute so the route does not depend on the process's working directory.
# backend/assets/asset_routes.py -> parents[2] is the api/ directory itself.
CLIPS_DIRECTORY = os.getenv(
    "CLIPS_DIRECTORY",
    str(Path(__file__).resolve().parents[2] / "assets" / "clips"),
)


# Serve one clip's video file
# Example: /assets/clips/super_cool_clip.mp4
@assets.route("/assets/clips/<path:filename>", methods=["GET"])
def get_clip_file(filename):
    current_app.logger.info(f'GET /assets/clips/{filename}')
    # send_from_directory refuses paths that escape the directory, so a
    # clip_url of "/../.env" cannot be used to read the API's own files.
    # A file that isn't there raises NotFound, which Flask turns into a 404.
    return send_from_directory(CLIPS_DIRECTORY, filename)
