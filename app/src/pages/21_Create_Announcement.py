import datetime
import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

# API endpoint that inserts a row into the announcement table
API_URL = "http://web-api:4000/talent_scout/announcement"

st.title('Create Announcement')
st.write('Post a platform-wide announcement and schedule when it should be visible.')

# announcement.user_id is a foreign key to administrator, so we post the
# logged-in admin's user_id from the session.
user_id = st.session_state.get('user_id')

with st.form('create_announcement_form'):
    title = st.text_input('Title *')
    body = st.text_area('Body')

    col1, col2 = st.columns(2)
    today = datetime.date.today()

    with col1:
        start_date = st.date_input('Start Date *', value=today)
        start_time = st.time_input('Start Time *', value=datetime.time(0, 0))

    with col2:
        end_date = st.date_input('End Date *', value=today + datetime.timedelta(days=7))
        end_time = st.time_input('End Time *', value=datetime.time(0, 0))

    submitted = st.form_submit_button('Post Announcement', type='primary')

if submitted:
    scheduled_start = datetime.datetime.combine(start_date, start_time)
    scheduled_end = datetime.datetime.combine(end_date, end_time)

    if not title:
        st.error('Please provide a title for the announcement.')
    elif scheduled_end <= scheduled_start:
        st.error('The scheduled end must come after the scheduled start.')
    elif user_id is None:
        st.error('No logged-in administrator found. Please log in again.')
    else:
        announcement_data = {
            "user_id": user_id,
            "title": title,
            "body": body if body else None,
            # DATETIME columns expect 'YYYY-MM-DD HH:MM:SS'
            "scheduled_start": scheduled_start.strftime('%Y-%m-%d %H:%M:%S'),
            "scheduled_end": scheduled_end.strftime('%Y-%m-%d %H:%M:%S'),
        }

        try:
            response = requests.post(API_URL, json=announcement_data)

            if response.status_code == 201:
                st.success(
                    f"Announcement created successfully "
                    f"(ID {response.json().get('announcement_id')})."
                )
            else:
                st.error(
                    f"Failed to create announcement: "
                    f"{response.json().get('error', 'Unknown error')}"
                )
        except requests.exceptions.RequestException as e:
            logger.error(f'Error posting announcement: {e}')
            st.error(f'Error connecting to the API: {str(e)}')
            st.info('Please ensure the API server is running')
