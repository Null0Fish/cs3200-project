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

# One column per destination, so the buttons sit side by side across the page
# instead of stacking into four full-width bars.
feed_col, accounts_col, rosters_col, announce_col = st.columns(4)

with feed_col:
    if st.button('Moderation Feed',
                 type='primary',
                 use_container_width=True):
        st.switch_page('pages/22_Moderation_Feed.py')

with accounts_col:
    if st.button('Manage Accounts',
                 type='primary',
                 use_container_width=True):
        st.switch_page('pages/23_Manage_Accounts.py')

with rosters_col:
    if st.button('Manage Rosters',
                 type='primary',
                 use_container_width=True):
        st.switch_page('pages/25_Manage_Rosters.py')

with announce_col:
    if st.button('Create Announcement',
                 type='primary',
                 use_container_width=True):
        st.switch_page('pages/21_Create_Announcement.py')
