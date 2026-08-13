"""
The athlete's upload form (story 1.3).

The video goes up with the caption in one multipart request, so the API can name
the file after the clip_id it creates and record it in the clip's clip_url. A
clip is never left in the feed as a row nobody can watch.
"""
import datetime
import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st

from modules.api import api_error
from modules.clips import CLIP_API_URL, VIDEO_TYPES
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title("Upload a Clip")

user_id = st.session_state['user_id']

with st.form("upload_clip_form"):
    st.subheader("Clip Details")

    caption = st.text_input("Caption *")
    posted_at = st.date_input("Date posted", value=datetime.date.today())
    video = st.file_uploader("Video *", type=VIDEO_TYPES)

    submitted = st.form_submit_button("Upload Clip")

    if submitted:
        if not caption:
            st.error("Please enter a caption")
        elif video is None:
            st.error("Please choose a video file")
        else:
            try:
                response = requests.post(
                    CLIP_API_URL,
                    data={
                        "user_id": user_id,
                        "caption": caption,
                        "posted_at": str(posted_at),
                    },
                    files={"video": (video.name, video.getvalue(), video.type)},
                    timeout=30,
                )

                if response.status_code == 201:
                    st.success("Clip uploaded!")
                    # The freshly uploaded file, straight from the uploader —
                    # no round trip to the API needed to show it back.
                    st.video(video)
                else:
                    st.error(f"Failed to upload clip: {api_error(response)}")

            except requests.exceptions.RequestException as e:
                logger.error(f'POST /clip failed: {e}')
                st.error(f"Error connecting to the API: {str(e)}")
                st.info("Please ensure the API server is running")

if st.button("View My Clips"):
    st.switch_page('pages/02_My_Clips.py')
