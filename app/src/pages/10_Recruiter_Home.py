import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title(f"Welcome Valued Recruiter, {st.session_state['first_name']}.")
st.write('### Ready to get scouting?')

if st.button('View Profile',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/11_Recruiter_Profile.py')

if st.button('Add Roster',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/12_Add_Roster.py')

if st.button('View Clips',
            type='primary',
            use_container_width=True):
    st.switch_page('pages/13_View_Clips.py')
