##################################################
# This is the main/entry-point file for the
# sample application for your project
##################################################

# Set up basic logging infrastructure
import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# import the main streamlit library as well
# as SideBarLinks function from src/modules folder
import requests
import streamlit as st
from modules.nav import SideBarLinks

# streamlit supports regular and wide layout (how the controls
# are organized/displayed on the screen).
st.set_page_config(layout='wide')

# API endpoint that reads the announcement table
ANNOUNCEMENT_API_URL = "http://web-api:4000/talent_scout/announcement"


@st.dialog("📣 Announcement")
def show_announcement_dialog(announcement):
    """Renders one announcement as a modal over whatever is on the page."""
    st.markdown(f"### {announcement['title']}")

    if announcement.get('body'):
        st.write(announcement['body'])

    posted_by = ' '.join(
        part for part in (announcement.get('first_name'),
                          announcement.get('last_name')) if part
    )
    if posted_by:
        st.caption(f"Posted by {posted_by}")

    if st.button('Got it', type='primary', use_container_width=True):
        st.rerun()


def get_active_announcement():
    """
    Returns the announcement to display, or None if there isn't one.

    active=true asks the API for only the announcements whose scheduled window
    contains the current time. More than one can be active at once, so the
    lowest announcement_id wins - that way every user sees the same one.
    """
    response = requests.get(ANNOUNCEMENT_API_URL, params={'active': 'true'}, timeout=5)
    response.raise_for_status()

    announcements = response.json()
    if not announcements:
        return None

    return min(announcements, key=lambda a: a['announcement_id'])

# If a user is at this page, we assume they are not
# authenticated.  So we change the 'authenticated' value
# in the streamlit session_state to false.
st.session_state['authenticated'] = False

# Use the SideBarLinks function from src/modules/nav.py to control
# the links displayed on the left-side panel.
# IMPORTANT: ensure src/.streamlit/config.toml sets
# showSidebarNavigation = false in the [client] section
SideBarLinks(show_home=True)

# ***************************************************
#    The major content of this page
# ***************************************************

logger.info("Loading the Home page of the app")
st.title('TalentScout')
st.write('#### Hi! As which user would you like to log in?')

# Every persona passes through this page on the way in, so showing the current
# announcement here is how it reaches all users. It is shown once per session:
# dismissing a dialog triggers a rerun, so the "already shown" flag has to be
# set before opening it or the dialog would immediately reopen.
if not st.session_state.get('announcement_shown'):
    st.session_state['announcement_shown'] = True
    try:
        active_announcement = get_active_announcement()
    except requests.exceptions.RequestException as e:
        # A missing API should not stop anyone from logging in.
        logger.warning(f'Could not load announcements: {e}')
        active_announcement = None

    if active_announcement:
        logger.info(f"Showing announcement {active_announcement['announcement_id']}")
        show_announcement_dialog(active_announcement)

# For each of the user personas for which we are implementing
# functionality, we put a button on the screen that the user
# can click to MIMIC logging in as that mock user.
#
# One column per persona puts the three side by side instead of stacked, so
# each button is a third of the page wide rather than the full width.
# use_container_width fills the column, which keeps all three the same size
# however long the label is.
athlete_col, recruiter_col, admin_col = st.columns(3)

with athlete_col:
    if st.button("Act as Bethany, a High School Athlete",
                 type='primary',
                 use_container_width=True):
        # when user clicks the button, they are now considered authenticated
        st.session_state['authenticated'] = True
        # we set the role of the current user
        st.session_state['role'] = 'athlete'
        # we add the first name of the user (so it can be displayed on
        # subsequent pages).
        st.session_state['first_name'] = 'Bethany'
        st.session_state['user_id'] = 1
        # finally, we ask streamlit to switch to another page, in this case, the
        # landing page for this particular user type
        logger.info("Logging in as High School Athlete Persona")
        st.switch_page('pages/00_Athlete_Home.py')

with recruiter_col:
    if st.button('Act as Kevin, a College Recruiter',
                 type='primary',
                 use_container_width=True):
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'recruiter'
        st.session_state['first_name'] = 'Kevin'
        st.session_state['user_id'] = 2
        st.switch_page('pages/10_Recruiter_Home.py')

with admin_col:
    if st.button('Act as Johnathan, a System Administrator',
                 type='primary',
                 use_container_width=True):
        st.session_state['authenticated'] = True
        st.session_state['role'] = 'administrator'
        st.session_state['first_name'] = 'Johnathan'
        st.session_state['user_id'] = 3
        st.switch_page('pages/20_Admin_Home.py')
