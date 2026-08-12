import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title(f"Welcome Elite Athlete, {st.session_state['first_name']}.")
st.write('### What would you like to do today superstar?')

if st.button('View Profile',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/01_Athlete_Profile.py')

if st.button('View My Clips',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/02_My_Clips.py')

if st.button('Upload New Clips',
            type='primary',
            use_container_width=True):
    st.switch_page('pages/03_Upload_Clips.py')
