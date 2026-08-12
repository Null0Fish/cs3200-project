import streamlit as st
import requests
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

# set up the page
st.title("My Clips")

API_URL = "http://web-api:4000/talent_scout/clip"
user_id = st.session_state['user_id']



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

                    # Story 1.3 - the "edit" link under each clip in Wireframe 2
                    new_caption = st.text_input(
                        "Caption",
                        value=clip["caption"],
                        key=f"caption_{clip_id}",
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("Save Caption", key=f"save_{clip_id}"):
                            put_response = requests.put(
                                f"{API_URL}/{clip_id}",
                                json={"caption": new_caption},
                            )
                            if put_response.status_code == 200:
                                st.success("Caption updated")
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
    else:
        st.error(
            f"Failed to fetch clips: {response.json().get('error', 'Unknown error')}"
        )

except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running")

if st.button("Upload a New Clip"):
    st.switch_page('pages/03_Upload_Clips.py')
