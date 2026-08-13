import logging
import requests
logger = logging.getLogger(__name__)
import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Call the SideBarLinks from the nav module in the modules directory
SideBarLinks()


API_URL = "http://web-api:4000/talent_scout/athlete/%s" % st.session_state['user_id']


# set the header of the page
st.header('Athlete Profile')

# You can access the session state to make a more customized/personalized app experience
st.write(f"### Hi, {st.session_state['first_name']}.")

# get the countries from the world bank data

try:
    # Send GET request to API
    response = requests.get(API_URL)

    if response.status_code == 200:
        # Store athlete data and show profile
        st.session_state.show_athlete_profile = True
        athlete = response.json()
        st.write(f"**GPA:** {float(athlete['gpa']):.2f}")
        st.write(f"**Graduation year:** {athlete['graduation_year']}")
        st.write(f"**Height:** {athlete['height_cm']} cm")
        st.write(f"**Weight:** {athlete['weight_kg']} kg")
        st.write(f"**Status:** {athlete['recruitment_status']}")

    else:
        st.error(
            f"Failed to fetch athlete data: {response.json().get('error', 'Unknown error')}"
        )

except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running")

st.subheader("Update My Metrics")

with st.form("update_metrics_form"):
    gpa = st.number_input("GPA", min_value=0.00, max_value=4.00,
                            value=float(athlete["gpa"]), step=0.01, format="%.2f")
    height_cm = st.number_input("Height (cm)", min_value=100, max_value=250,
                                value=int(athlete["height_cm"]))
    weight_kg = st.number_input("Weight (kg)", min_value=30, max_value=200,
                                value=int(athlete["weight_kg"]))
    graduation_year = st.number_input("Graduation Year", min_value=2024, max_value=2040,
                                        value=int(athlete["graduation_year"]))

    submitted = st.form_submit_button("Save Changes")

    if submitted:
        try:
            put_response = requests.put(API_URL, json={
                "gpa": float(gpa),
                "height_cm": int(height_cm),
                "weight_kg": int(weight_kg),
                "graduation_year": int(graduation_year),
            })
            if put_response.status_code == 200:
                st.success("Profile updated")
                st.rerun()
            else:
                st.error(
                    f"Failed to update: {put_response.json().get('error', 'Unknown error')}"
                )
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the API: {str(e)}")



st.subheader("Recruitment Status")

status_options = ["open", "committed", "inactive"]
new_status = st.selectbox(
    "My status",
    status_options,
    index=status_options.index(athlete["recruitment_status"])
    if athlete["recruitment_status"] in status_options else 0,
)

if st.button("Update Status"):
    try:
        status_response = requests.put(API_URL, json={"recruitment_status": new_status})
        if status_response.status_code == 200:
            st.success(f"Status updated to {new_status}")
            st.rerun()
        else:
            st.error(
                f"Failed to update status: {status_response.json().get('error', 'Unknown error')}"
            )
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")