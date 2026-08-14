import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title(f"Welcome Elite Athlete, {st.session_state['first_name']}.")
st.write('### What would you like to do today superstar?')

# One column per destination, so the buttons sit side by side across the page
# instead of stacking into three full-width bars.
profile_col, clips_col, upload_col = st.columns(3)

with profile_col:
    if st.button('View Profile',
                 type='primary',
                 use_container_width=True):
        st.switch_page('pages/01_Athlete_Profile.py')

with clips_col:
    if st.button('View My Clips',
                 type='primary',
                 use_container_width=True):
        st.switch_page('pages/02_My_Clips.py')

with upload_col:
    if st.button('Upload New Clips',
                 type='primary',
                 use_container_width=True):
        st.switch_page('pages/03_Upload_Clips.py')
