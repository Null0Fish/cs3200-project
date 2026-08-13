import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.write("# About this App")

st.markdown(
    """
    **TalentScout** is a bidirectional recruiting platform for high school athletes
    and college recruiters, built by Team Purplicious for CS 3200 (Summer B 2026).

    Athletes publish their metrics, personal records, and highlight clips.
    Recruiters post the rosters and openings they need to fill and scroll a feed of
    clips to find talent. Both sides can see who has been looking at them.

    The app runs on Streamlit, talks to a Flask REST API, and stores everything in
    MySQL — see the repository README for the full route map.
    """
)

# Add a button to return to home page
if st.button("Return to Home", type="primary"):
    st.switch_page("Home.py")
