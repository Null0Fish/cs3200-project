import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title("Add Roster")

# API endpoints
API_BASE_URL = "http://web-api:4000/talent_scout"

# Fetch available sports
try:
    sports_response = requests.get(f"{API_BASE_URL}/sports")
    sports_response.raise_for_status()
    sports_list = sports_response.json()
    sport_options = {sport.get("name", "Unknown"): sport.get("sport_id") for sport in sports_list}
except Exception as e:
    st.error(f"Could not load sports: {str(e)}")
    sport_options = {}

with st.form("add_roster_form"):
    team_name = st.text_input("Team Name")
    sport_name = st.selectbox("Sport", list(sport_options.keys()) if sport_options else [])
    gender = st.selectbox("Gender", ["Male", "Female", "Co-ed"])
    division = st.text_input("Division")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    
    submitted = st.form_submit_button("Add Roster")
    
    if submitted:
        if not team_name or not sport_name:
            st.error("Team Name and Sport are required")
        else:
            try:
                create_response = requests.post(
                    f"{API_BASE_URL}/roster",
                    json={
                        "user_id": st.session_state['user_id'],
                        "sport_id": sport_options[sport_name],
                        "team_name": team_name,
                        "gender": gender,
                        "division": division,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                )
                
                if create_response.status_code == 201:
                    st.success("Roster created successfully!")
                    st.switch_page('pages/11_Recruiter_Profile.py')
                else:
                    st.error(f"Failed to create roster: {create_response.json().get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error creating roster: {str(e)}")
