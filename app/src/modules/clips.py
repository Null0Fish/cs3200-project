"""
Shared helpers for the pages that show highlight clips.

There are two different addresses for the same API here, and mixing them up is
the easiest way to end up with a clip that looks broken:

  CLIP_API_URL      is called by Streamlit, from inside the app container, so
                    it uses the `web-api` hostname on the compose network.
  CLIP_VIDEO_BASE   goes into the page as a video source and is fetched by the
                    viewer's browser, which is not on that network and cannot
                    resolve `web-api`. It has to be an address the host can
                    reach — the port docker-compose.yaml publishes.

Override CLIP_VIDEO_BASE_URL in the environment when the API is not on
localhost, e.g. when the stack is deployed behind a domain.
"""
import os

import streamlit as st

CLIP_API_URL = "http://web-api:4000/talent_scout/clip"

CLIP_VIDEO_BASE = os.getenv("CLIP_VIDEO_BASE_URL", "http://localhost:4000/clips")


def clip_video_url(clip_id):
    """The browser-facing URL of one clip's video file."""
    return f"{CLIP_VIDEO_BASE}/{clip_id}"


def show_clip_video(clip):
    """
    Render a clip's video, or a note in its place if it hasn't got one.

    The API reports has_video by looking for the file on disk, so this never
    points a player at a URL that would 404. Clips created before videos were
    stored (and the seeded ones) land in the else branch.
    """
    if clip.get("has_video"):
        st.video(clip_video_url(clip["clip_id"]))
    else:
        st.info("No video on this clip yet.")
