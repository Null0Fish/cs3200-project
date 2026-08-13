import datetime
import streamlit as st
import requests
from modules.nav import SideBarLinks
from modules.clips import CLIP_API_URL

st.set_page_config(layout='wide')

SideBarLinks()

st.title("Upload a Clip")

user_id = st.session_state['user_id']

# Matches the extensions the API is willing to store (see clip_storage.py).
VIDEO_TYPES = ["mp4", "webm", "ogg", "mov", "m4v"]


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
            clip_data = {
                "user_id": user_id,
                "caption": caption,
                "posted_at": str(posted_at),
            }

            try:
                # The video goes up with the caption in one multipart request,
                # so the API can name the file after the clip_id it creates and
                # never has a clip row sitting around without a video.
                response = requests.post(
                    CLIP_API_URL,
                    data=clip_data,
                    files={"video": (video.name, video.getvalue(), video.type)},
                )

                if response.status_code == 201:
                    st.success("Clip uploaded!")
                    st.video(video)
                else:
                    st.error(
                        f"Failed to upload clip: {response.json().get('error', 'Unknown error')}"
                    )

            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {str(e)}")
                st.info("Please ensure the API server is running")

if st.button("View My Clips"):
    st.switch_page('pages/02_My_Clips.py')
