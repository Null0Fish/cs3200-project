import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.moderation import require_admin
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()
require_admin()

st.title(f"Welcome, {st.session_state['first_name']}.")
st.write('### What would you like to do today?')

if st.button('Moderation Feed',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/22_Moderation_Feed.py')

if st.button('Manage Accounts',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/23_Manage_Accounts.py')

if st.button('Manage Rosters',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/25_Manage_Rosters.py')

if st.button('Create Announcement',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/21_Create_Announcement.py')
