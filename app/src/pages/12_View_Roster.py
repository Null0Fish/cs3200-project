import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# API endpoints
API_BASE_URL = "http://web-api:4000/talent_scout"

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title("Roster Details")

selected_roster_id = st.session_state.get("selected_roster_id")

if selected_roster_id is None:
    st.error("No roster selected")
    if st.button("Return to Profile"):
        st.switch_page("pages/11_Recruiter_Profile.py")
else:
    roster_url = f"{API_BASE_URL}/roster/{selected_roster_id}"

    try:
        response = requests.get(roster_url)

        if response.status_code == 200:
            roster = response.json()

            st.header(roster.get("team_name", "Roster"))

            st.write(f"**Division:** {roster.get('division', 'N/A')}")
            st.write(f"**Gender:** {roster.get('gender', 'N/A')}")

            st.subheader("Openings")
            openings = roster.get("openings", [])
            if openings:
                for opening in openings:
                    with st.expander(f"Opening {opening['opening_number']}"):
                        st.write(f"**Position:** {opening.get('position', 'N/A')}")
                        st.write(f"**Required GPA:** {opening.get('required_gpa', 'N/A')}")
                        st.write(
                            f"**Required Height:** {opening.get('required_height_cm', 'N/A')} cm"
                        )
                        st.write(f"**Graduation Year:** {opening.get('grad_year', 'N/A')}")
            else:
                st.info("No openings posted yet")

            st.subheader("Add Opening")
            with st.form("add_opening_form"):
                required_gpa = st.text_input("Required GPA")
                required_height_cm = st.text_input("Required Height (cm)")
                position = st.text_input("Position")
                grad_year = st.text_input("Graduation Year")

                submitted = st.form_submit_button("Add Opening")

                if submitted:
                    try:
                        create_response = requests.post(
                            f"{API_BASE_URL}/opening",
                            json={
                                "roster_id": selected_roster_id,
                                "required_gpa": float(required_gpa),
                                "required_height_cm": int(required_height_cm),
                                "position": position,
                                "grad_year": int(grad_year),
                            },
                        )

                        if create_response.status_code == 201:
                            st.success("Opening added successfully")
                            st.rerun()
                        else:
                            st.error(
                                f"Failed to add opening: {create_response.json().get('error', 'Unknown error')}"
                            )
                    except Exception as e:
                        st.error(f"Error connecting to the API: {str(e)}")
        else:
            st.error(f"Roster not found - API returned: {response.json()}")
            if st.button("Return to Profile"):
                st.switch_page("pages/11_Recruiter_Profile.py")

    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.info("Please ensure the API server is running")
