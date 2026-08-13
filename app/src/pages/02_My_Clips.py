"""
The athlete's own clips (story 1.3).

Each clip plays here and can be re-captioned, given a different video, or taken
down. Swapping the video keeps the clip_id, so the caption and any comments the
clip has collected survive the change.
"""
import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st

from modules.api import api_error, delete_resource, fetch, flash, show_flash
from modules.clips import CLIP_API_URL, VIDEO_TYPES, render_clip_video
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title("My Clips")

show_flash()

user_id = st.session_state['user_id']

clips = fetch('/clip', params={"athlete_id": user_id})
if clips is None:
    st.stop()

if not clips:
    st.info("You haven't uploaded any clips yet.")
else:
    st.write(f"**{len(clips)} clips**")

    for clip in clips:
        clip_id = clip["clip_id"]

        with st.expander(f"{clip['caption']} — posted {clip['posted_at']}"):
            render_clip_video(clip)

            new_caption = st.text_input(
                "Caption",
                value=clip["caption"],
                key=f"caption_{clip_id}",
            )

            save_col, delete_col = st.columns(2)

            with save_col:
                if st.button("Save Changes", key=f"save_{clip_id}"):
                    try:
                        put_response = requests.put(
                            f"{CLIP_API_URL}/{clip_id}",
                            json={"caption": new_caption},
                            timeout=10,
                        )
                    except requests.exceptions.RequestException as e:
                        logger.error(f'PUT /clip/{clip_id} failed: {e}')
                        st.error(f"Error connecting to the API: {str(e)}")
                    else:
                        if put_response.status_code == 200:
                            flash("Clip updated")
                            st.rerun()
                        else:
                            st.error(f"Failed to update: {api_error(put_response)}")

            with delete_col:
                if st.button("Delete Clip", key=f"delete_{clip_id}"):
                    delete_resource(f'/clip/{clip_id}', "Clip deleted")

            # A clip seeded without a video, or one whose cut has been bettered,
            # gets its file here. The API renames the upload after the clip_id
            # and points clip_url at it.
            label = "Replace video" if clip.get("clip_url") else "Add a video"
            new_video = st.file_uploader(
                label, type=VIDEO_TYPES, key=f"video_{clip_id}"
            )
            if new_video is not None and st.button(
                "Upload Video", key=f"upload_video_{clip_id}"
            ):
                try:
                    video_response = requests.put(
                        f"{CLIP_API_URL}/{clip_id}/video",
                        files={
                            "video": (
                                new_video.name,
                                new_video.getvalue(),
                                new_video.type,
                            )
                        },
                        timeout=30,
                    )
                except requests.exceptions.RequestException as e:
                    logger.error(f'PUT /clip/{clip_id}/video failed: {e}')
                    st.error(f"Error connecting to the API: {str(e)}")
                else:
                    if video_response.status_code == 200:
                        flash("Video uploaded")
                        st.rerun()
                    else:
                        st.error(
                            f"Failed to upload video: {api_error(video_response)}"
                        )

if st.button("Upload a New Clip"):
    st.switch_page('pages/03_Upload_Clips.py')
