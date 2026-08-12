import logging
import requests
from requests.exceptions import RequestException
logger = logging.getLogger(__name__)
import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Call the SideBarLinks from the nav module in the modules directory
SideBarLinks()

# API endpoints
API_BASE_URL = "http://web-api:4000/talent_scout"
API_URL = f"{API_BASE_URL}/recruiter/{st.session_state['user_id']}"

st.title("Recruiter Profile")
st.write(f"### Hi, {st.session_state['first_name']}.")


try:
    response = requests.get(API_URL)
    response.raise_for_status()

    recruiter = response.json()
    university = recruiter.get("university", {})
    rosters = recruiter.get("rosters", [])

    st.header(f"{recruiter['first_name']} {recruiter['last_name']}")

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Contact Information")
        st.write(f"**Email:** {recruiter['email']}")
        st.write(f"**Phone:** {recruiter.get('phone') or 'N/A'}")

    with right_col:
        st.subheader("University")
        st.write(f"**Name:** {university.get('name', 'N/A')}")
        st.write(f"**Website:** {university.get('website_url') or 'N/A'}")

    st.subheader("Rosters")
    if not rosters:
        st.info("No rosters found :(")
    else:
        roster_data = []
        roster_lookup = {}

        for roster in rosters:
            roster_id = roster.get("roster_id")
            if roster_id is None:
                continue

            views_response = requests.get(f"{API_BASE_URL}/roster_view/{roster_id}")
            views_response.raise_for_status()

            roster_lookup[roster_id] = roster
            roster_data.append(
                {
                    "Name": roster.get("team_name", "Roster"),
                    "Division": roster.get("division", "N/A"),
                    "Gender": roster.get("gender", "N/A"),
                    "Views": len(views_response.json()),
                }
            )

        st.dataframe(roster_data, hide_index=True, use_container_width=True)

        st.write("### Open a roster")
        for roster_id, roster in roster_lookup.items():
            if roster_id is None:
                continue

            button_col, = st.columns([1])
            with button_col:
                if st.button(
                    f"View {roster.get('team_name', 'Roster')}",
                    key=f"view_roster_{roster_id}",
                    use_container_width=True,
                ):
                    st.session_state["selected_roster_id"] = roster_id
                    st.switch_page("pages/12_View_Roster.py")
except Exception as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running")