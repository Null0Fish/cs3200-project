"""
The recruiter's clip feed (story 2.1).

Every clip on the platform, newest first. A clip whose clip_url is set plays
here; one without a video file attached shows its caption and comments only.
"""
import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st

from modules.api import (
    API_BASE_URL, api_error, fetch, flash, full_name, show_flash,
)
from modules.clips import render_clip_video
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title("Clip Feed")
st.caption("Scroll the clips, then open one to see the athlete behind it.")

show_flash()

user_id = st.session_state['user_id']


def show_clip_detail(clip_id):
    """
    Render the athlete's metrics and the clip's comments, with a reply box.

    The feed itself only carries what a card needs, so the metrics are pulled
    per clip and only once the recruiter has asked to see them (story 2.3) —
    fetching them for every clip up front would be one request per card on every
    page load.
    """
    detail = fetch(f'/clip/{clip_id}')
    if detail is None:
        return

    metrics = st.columns(5)
    metrics[0].metric("GPA", detail.get("gpa", "—"))
    metrics[1].metric("Height (cm)", detail.get("height_cm", "—"))
    metrics[2].metric("Weight (kg)", detail.get("weight_kg", "—"))
    metrics[3].metric("Class of", detail.get("graduation_year", "—"))
    metrics[4].metric("Status", detail.get("recruitment_status") or "—")

    comments = detail.get("comments", [])
    st.write(f"**Comments ({len(comments)})**")
    for comment in comments:
        st.markdown(f"- **{full_name(comment)}** — {comment['content']}")

    new_comment = st.text_input("Leave a comment", key=f"new_comment_{clip_id}")
    if st.button("Post Comment", key=f"post_comment_{clip_id}"):
        if not new_comment.strip():
            st.error("Write something first")
            return
        try:
            post_response = requests.post(
                f"{API_BASE_URL}/comment",
                json={
                    "clip_id": clip_id,
                    "user_id": user_id,
                    "content": new_comment,
                },
                timeout=10,
            )
        except requests.exceptions.RequestException as e:
            logger.error(f'POST /comment failed: {e}')
            st.error(f"Error connecting to the API: {str(e)}")
            return

        if post_response.status_code == 201:
            flash("Comment posted")
            st.rerun()
        else:
            st.error(f"Failed to post: {api_error(post_response)}")


clips = fetch('/clip')
if clips is None:
    st.stop()

if not clips:
    st.info("No clips available")
else:
    for clip in clips:
        clip_id = clip["clip_id"]
        athlete = full_name(clip, fallback=f"Athlete {clip['athlete_id']}")

        # The video is the point of the card, so it gets the wider column
        # and the text sits beside it rather than under it.
        video_col, info_col = st.columns([2, 3])

        with video_col:
            render_clip_video(clip)

        with info_col:
            st.subheader(athlete)
            st.write(clip["caption"])
            st.caption(f"Posted {clip['posted_at']}")

            # Kept behind a toggle because an expander's body runs whether
            # or not it is open, which would fetch every clip's detail on
            # every rerun.
            detail_key = f"show_detail_{clip_id}"
            if st.button("Athlete details & comments", key=f"detail_btn_{clip_id}"):
                st.session_state[detail_key] = not st.session_state.get(detail_key)

            if st.session_state.get(detail_key):
                show_clip_detail(clip_id)

        st.divider()
