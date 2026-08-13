import datetime
import streamlit as st
import requests
from modules.clips import normalize_clip_url
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title("Upload a Clip")

API_URL = "http://web-api:4000/talent_scout/clip"
user_id = st.session_state['user_id']





with st.form("upload_clip_form"):
    st.subheader("Clip Details")

    caption = st.text_input("Caption *")
    posted_at = st.date_input("Date posted", value=datetime.date.today())
    # The video file itself is not uploaded through the app: it is placed in the
    # API's assets/clips directory and named here, and the clip then plays from
    # /assets/clips/<file name>. Leaving this blank posts a clip with no video.
    clip_file = st.text_input(
        "Video file name",
        placeholder="dash_highlight.mp4",
        help="The file in the API's assets/clips directory that holds this clip's video.",
    )

    submitted = st.form_submit_button("Upload Clip")

    if submitted:
        if not caption:
            st.error("Please enter a caption")
        else:
            clip_data = {
                "user_id": user_id,
                "caption": caption,
                "posted_at": str(posted_at),
                "clip_url": normalize_clip_url(clip_file),
            }

            try:
                response = requests.post(API_URL, json=clip_data)

                if response.status_code == 201:
                    clip_id = response.json().get("clip_id")
                    st.success(f"Clip {clip_id} uploaded!")
                else:
                    st.error(
                        f"Failed to upload clip: {response.json().get('error', 'Unknown error')}"
                    )

            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {str(e)}")
                st.info("Please ensure the API server is running")

if st.button("View My Clips"):
    st.switch_page('pages/02_My_Clips.py')