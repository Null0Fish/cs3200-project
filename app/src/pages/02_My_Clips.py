import streamlit as st
import requests
from modules.clips import normalize_clip_url, render_clip_video
from modules.nav import SideBarLinks
from modules.clips import CLIP_API_URL, show_clip_video

st.set_page_config(layout='wide')

SideBarLinks()

# set up the page
st.title("My Clips")

API_URL = CLIP_API_URL
user_id = st.session_state['user_id']

# Matches the extensions the API is willing to store (see clip_storage.py).
VIDEO_TYPES = ["mp4", "webm", "ogg", "mov", "m4v"]



try:
    response = requests.get(API_URL, params={"athlete_id": user_id})

    if response.status_code == 200:
        clips = response.json()

        if not clips:
            st.info("You haven't uploaded any clips yet.")
        else:
            st.write(f"**{len(clips)} clips**")

            for clip in clips:
                clip_id = clip["clip_id"]

                with st.expander(f"{clip['caption']} — posted {clip['posted_at']}"):

                    show_clip_video(clip)

                    # Story 1.3 - the "edit" link under each clip in Wireframe 2
                    new_caption = st.text_input(
                        "Caption",
                        value=clip["caption"],
                        key=f"caption_{clip_id}",
                    )
                    # Clearing this field detaches the video from the clip; the
                    # clip and its comments stay.
                    new_clip_file = st.text_input(
                        "Video file name",
                        value=(clip.get("clip_url") or "").lstrip("/"),
                        placeholder="dash_highlight.mp4",
                        key=f"clip_url_{clip_id}",
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("Save Changes", key=f"save_{clip_id}"):
                            put_response = requests.put(
                                f"{API_URL}/{clip_id}",
                                json={
                                    "caption": new_caption,
                                    "clip_url": normalize_clip_url(new_clip_file),
                                },
                            )
                            if put_response.status_code == 200:
                                st.success("Clip updated")
                                st.rerun()
                            else:
                                st.error(
                                    f"Failed to update: {put_response.json().get('error', 'Unknown error')}"
                                )

                    with col2:
                        if st.button("Delete Clip", key=f"delete_{clip_id}"):
                            delete_response = requests.delete(f"{API_URL}/{clip_id}")
                            if delete_response.status_code == 200:
                                st.success("Clip deleted")
                                st.rerun()
                            else:
                                st.error(
                                    f"Failed to delete: {delete_response.json().get('error', 'Unknown error')}"
                                )

                    # Swapping the video keeps the clip_id, so the caption and
                    # any comments the clip has collected survive the change.
                    label = "Replace video" if clip["has_video"] else "Add a video"
                    new_video = st.file_uploader(
                        label, type=VIDEO_TYPES, key=f"video_{clip_id}"
                    )
                    if new_video is not None and st.button(
                        "Upload Video", key=f"upload_video_{clip_id}"
                    ):
                        video_response = requests.put(
                            f"{API_URL}/{clip_id}/video",
                            files={
                                "video": (
                                    new_video.name,
                                    new_video.getvalue(),
                                    new_video.type,
                                )
                            },
                        )
                        if video_response.status_code == 200:
                            st.success("Video uploaded")
                            st.rerun()
                        else:
                            st.error(
                                f"Failed to upload video: {video_response.json().get('error', 'Unknown error')}"
                            )
    else:
        st.error(
            f"Failed to fetch clips: {response.json().get('error', 'Unknown error')}"
        )

except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running")

if st.button("Upload a New Clip"):
    st.switch_page('pages/03_Upload_Clips.py')
