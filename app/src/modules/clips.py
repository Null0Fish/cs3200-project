"""
Rendering a highlight clip's video.

A clip row carries an optional clip_url: the name of its video file underneath
the API's /assets/clips directory, stored with a leading slash. A NULL clip_url
means the athlete created the clip entry but never attached a video, so there is
nothing to play — every page that shows clips has to handle both cases.

There are two different addresses for the same API here, and mixing them up is
the easiest way to end up with a clip that looks broken:

  CLIP_API_URL        is called by Streamlit, from inside the app container, so
                      it uses the `web-api` hostname on the compose network.
  CLIP_ASSET_BASE_URL goes into the page as a video source and is fetched by the
                      viewer's browser, which is not on that network and cannot
                      resolve `web-api`. It has to be an address the host can
                      reach — the port docker-compose.yaml publishes.

Override CLIP_ASSET_BASE_URL in the environment when the API is published
somewhere other than localhost:4000.
"""
import os

import streamlit as st

from modules.api import API_BASE_URL

# Extensions the API is willing to store (see api/backend/clips/clip_storage.py).
VIDEO_TYPES = ["mp4", "webm", "ogg", "mov", "m4v"]

CLIP_API_URL = f"{API_BASE_URL}/clip"

CLIP_ASSET_BASE_URL = os.getenv(
    "CLIP_ASSET_BASE_URL", "http://localhost:4000/assets/clips"
)


def normalize_clip_url(value):
    """
    Turn what someone typed into a form the clip_url column expects.

    Blank input becomes None (no video attached), and a file name is given the
    leading slash that clip_url is stored with, so "dash.mp4" and "/dash.mp4"
    both end up as "/dash.mp4".
    """
    filename = (value or "").strip()
    if not filename:
        return None
    return filename if filename.startswith("/") else f"/{filename}"


def clip_video_url(clip_url):
    """The absolute URL the browser loads a clip's video file from."""
    return f"{CLIP_ASSET_BASE_URL}{clip_url}"


def render_clip_video(clip):
    """
    Render a clip's video, or a note explaining that there is nothing to play.

    st.video is given the asset URL rather than the file's bytes: handing it a
    URL means the browser fetches the video straight from the API instead of the
    Streamlit server reading it over HTTP and serving it a second time.
    """
    clip_url = clip.get("clip_url")
    if not clip_url:
        st.caption("No video file is attached to this clip.")
        return
    st.video(clip_video_url(clip_url))
