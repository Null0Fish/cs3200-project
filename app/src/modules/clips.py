"""
Rendering a highlight clip's video.

A clip row carries an optional clip_url: the name of its video file underneath
the API's /assets/clips directory, stored with a leading slash. A NULL clip_url
means the athlete created the clip entry but never attached a video, so there is
nothing to play — every page that shows clips has to handle both cases.

The <video> element is loaded by the *browser*, not by the Streamlit server, so
its src cannot use the web-api Docker hostname the rest of the app calls. It has
to be an address the browser can reach: the API's published host port. Override
CLIP_ASSET_BASE_URL if the API is published somewhere other than localhost:4000.
"""
import html
import os

import streamlit as st

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


def render_clip_video(clip, max_width=640):
    """
    Render clip's video, or a note explaining that there is nothing to play.

    The URL is escaped before going into the attribute: clip_url is athlete-
    supplied text, and a stray quote in it would otherwise break out of the src.
    """
    clip_url = clip.get("clip_url")
    if not clip_url:
        st.caption("No video file is attached to this clip.")
        return

    src = html.escape(clip_video_url(clip_url), quote=True)
    st.html(
        f'<video src="{src}" controls preload="metadata" '
        f'style="width: 100%; max-width: {max_width}px; border-radius: 4px;">'
        f'</video>'
    )
