"""
Writing highlight clip video files.

The clip row goes in MySQL; the video bytes go on disk under api/assets/clips
and are served straight back out by the assets blueprint. Keeping the bytes out
of the database is what makes that route so cheap — a BLOB column would mean
carrying the file's type and size as extra columns and pushing the whole video
back through the connection on every play, while a file on disk can be streamed
to the browser.

Which file belongs to which clip is recorded in clip.clip_url, the name of the
file with a leading slash. This module only handles the write side: naming an
upload, saving it, and removing it again. asset_routes.py owns the directory and
the read side, and is imported from here so both agree on where the files are.

An upload is named after the clip_id it belongs to, keeping the extension it
arrived with (clip 12 uploaded as race.mp4 becomes /12.mp4). The uploaded name
is never used on disk, so a hostile one cannot escape the directory. Files
dropped into api/assets/clips by hand keep whatever name they were given — the
seed data's /super_cool_clip.mp4, for instance — which is why the name has to be
stored rather than derived from the clip_id.
"""
from pathlib import Path

from backend.assets.asset_routes import CLIPS_DIRECTORY

# Extensions a browser <video> element can be expected to play.
ALLOWED_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov", ".m4v"}

# 64 MB. Highlight clips are a few seconds long, so this is generous for one
# and still small enough that a runaway upload can't fill the container's disk.
MAX_CLIP_BYTES = 64 * 1024 * 1024


def clips_directory():
    """The directory holding clip videos, created on first use."""
    directory = Path(CLIPS_DIRECTORY)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def clip_file_path(clip_url):
    """
    The file a clip_url points at, or None if the column is NULL/empty.

    clip_url is athlete-supplied, so only its final component is trusted: a
    value of "/../.env" resolves to a file named ".env" inside the clips
    directory rather than one above it.
    """
    name = Path((clip_url or "").strip()).name
    if not name:
        return None
    return clips_directory() / name


def save_clip_file(clip_id, upload):
    """
    Write an uploaded video to disk as <clip_id><extension>.

    `upload` is the werkzeug FileStorage that came out of request.files. Returns
    the clip_url to store on the row. Raises ValueError if the extension isn't
    one we serve.
    """
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported video type '{extension or upload.filename}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    filename = f"{int(clip_id)}{extension}"
    upload.save(clips_directory() / filename)
    return f"/{filename}"


def delete_clip_file(clip_url):
    """
    Remove the file a clip_url points at. Returns whether one was deleted.

    Only files this module named — <clip_id>.<ext> — are removed. A clip
    pointing at a hand-placed file such as /super_cool_clip.mp4 may not be the
    only clip pointing at it, so deleting that clip leaves the file alone.
    """
    path = clip_file_path(clip_url)
    if path is None or not path.is_file() or not path.stem.isdigit():
        return False
    path.unlink()
    return True
