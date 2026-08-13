import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st
from modules.nav import SideBarLinks
from modules.clips import CLIP_API_URL, show_clip_video

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title("Clip Feed")
st.caption("Scroll the clips, then open one to see the athlete behind it.")

COMMENT_API_URL = "http://web-api:4000/talent_scout/comment"

user_id = st.session_state['user_id']


def load_clip_detail(clip_id):
    """
    Fetch one clip's athlete metrics and comment thread (story 2.3).

    The feed itself only carries what a card needs, so the metrics are pulled
    per clip and only once the recruiter has asked to see them — fetching them
    for every clip up front would be one request per card on every page load.
    """
    response = requests.get(f"{CLIP_API_URL}/{clip_id}", timeout=5)
    response.raise_for_status()
    return response.json()


def show_clip_detail(clip_id):
    """Render the athlete's metrics and the clip's comments, with a reply box."""
    try:
        detail = load_clip_detail(clip_id)
    except requests.exceptions.RequestException as e:
        logger.warning(f'Could not load detail for clip {clip_id}: {e}')
        st.error("Could not load this athlete's details.")
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
        author = ' '.join(
            part for part in (comment.get('first_name'), comment.get('last_name'))
            if part
        ) or 'Deleted user'
        st.markdown(f"- **{author}** — {comment['content']}")

    new_comment = st.text_input("Leave a comment", key=f"new_comment_{clip_id}")
    if st.button("Post Comment", key=f"post_comment_{clip_id}"):
        if not new_comment.strip():
            st.error("Write something first")
        else:
            post_response = requests.post(
                COMMENT_API_URL,
                json={
                    "clip_id": clip_id,
                    "user_id": user_id,
                    "content": new_comment,
                },
            )
            if post_response.status_code == 201:
                st.success("Comment posted")
                st.rerun()
            else:
                st.error(
                    f"Failed to post: {post_response.json().get('error', 'Unknown error')}"
                )


try:
    response = requests.get(CLIP_API_URL, timeout=5)
    response.raise_for_status()

    clips = response.json()

    if not clips:
        st.info("No clips available")
    else:
        for clip in clips:
            clip_id = clip["clip_id"]
            athlete = ' '.join(
                part for part in (clip.get('first_name'), clip.get('last_name'))
                if part
            ) or f"Athlete {clip['athlete_id']}"

            # The video is the point of the card, so it gets the wider column
            # and the text sits beside it rather than under it.
            video_col, info_col = st.columns([2, 3])

            with video_col:
                show_clip_video(clip)

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

except requests.exceptions.RequestException as e:
    st.error(f"Error loading clips: {str(e)}")
    st.info("Please ensure the API server is running")
