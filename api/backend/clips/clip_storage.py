"""
Where highlight clip video files live.

The clip row goes in MySQL; the video bytes go on disk and are served back out
at /clips/<clip_id>. Keeping the bytes out of the database is what makes that
route so cheap — a BLOB column would mean carrying the file's type and size as
extra columns and pushing the whole video back through the connection on every
play, while a file on disk can be streamed straight to the browser.

A clip's file is named after its clip_id and keeps the extension it arrived
with (clip 12 uploaded as race.mp4 becomes 12.mp4). That naming is the only
bookkeeping the scheme needs: the extension on disk gives the Content-Type, and
the presence of the file says whether the clip has a video at all. Nothing about
the file has to be recorded in the database, so a page that wants to show a clip
can build <video src="/clips/12"> from the clip_id it already has.
"""
import os
from pathlib import Path

# Extensions a browser <video> element can be expected to play. The uploaded
# filename is only ever read for its extension — the file itself is renamed to
# the clip_id, so a hostile name can never reach the file system.
ALLOWED_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov", ".m4v"}

# 64 MB. Highlight clips are a few seconds long, so this is generous for one
# and still small enough that a runaway upload can't fill the container's disk.
MAX_CLIP_BYTES = 64 * 1024 * 1024


def clip_storage_dir():
    """
    The directory holding clip videos, created on first use.

    Defaults to a directory under /apicode, which docker-compose.yaml
    bind-mounts from ./api, so uploads in dev survive a container restart.
    Override with the CLIP_STORAGE_DIR environment variable.
    """
    directory = Path(os.getenv("CLIP_STORAGE_DIR", "/apicode/clip-files"))
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def find_clip_file(clip_id):
    """The stored video for one clip, or None if it never got one."""
    for path in clip_storage_dir().glob(f"{int(clip_id)}.*"):
        if path.is_file():
            return path
    return None


def clip_ids_with_video():
    """
    Every clip_id that has a video on disk, from a single scan of the directory.

    The feed needs a has_video flag for each clip it returns, and one directory
    scan is cheaper than one lookup per clip.
    """
    return {
        int(path.stem)
        for path in clip_storage_dir().iterdir()
        if path.is_file() and path.stem.isdigit()
    }


def save_clip_file(clip_id, upload):
    """
    Write an uploaded video to disk as <clip_id><extension>.

    `upload` is the werkzeug FileStorage that came out of request.files. Raises
    ValueError if the extension isn't one we serve. Any file already stored for
    this clip is removed first, so re-uploading with a different extension can't
    leave two files both claiming the same clip_id.
    """
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported video type '{extension or upload.filename}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    delete_clip_file(clip_id)
    path = clip_storage_dir() / f"{int(clip_id)}{extension}"
    upload.save(path)
    return path


def delete_clip_file(clip_id):
    """Remove a clip's video if it has one. Returns whether a file was deleted."""
    path = find_clip_file(clip_id)
    if path is None:
        return False
    path.unlink()
    return True
