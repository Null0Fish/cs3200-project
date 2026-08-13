# Idea borrowed from https://github.com/fsmosca/sample-streamlit-authenticator

# This file has functions to add links to the left sidebar based on the user's role.

import streamlit as st


# ---- General ----------------------------------------------------------------

def home_nav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")


def about_page_nav():
    st.sidebar.page_link("pages/30_About.py", label="About", icon="🧠")


# ---- Role: athlete ----------------------------------------------------------

def athlete_home_nav():
    st.sidebar.page_link("pages/00_Athlete_Home.py", label="Athlete Home", icon="🏃")


def athlete_profile_nav():
    st.sidebar.page_link("pages/01_Athlete_Profile.py", label="My Profile", icon="👤")


def my_clips_nav():
    st.sidebar.page_link("pages/02_My_Clips.py", label="My Clips", icon="🎬")


def upload_clips_nav():
    st.sidebar.page_link("pages/03_Upload_Clips.py", label="Upload a Clip", icon="⬆️")


# ---- Role: recruiter --------------------------------------------------------

def recruiter_home_nav():
    st.sidebar.page_link("pages/10_Recruiter_Home.py", label="Recruiter Home", icon="🔎")


def recruiter_profile_nav():
    st.sidebar.page_link("pages/11_Recruiter_Profile.py", label="My Profile", icon="👤")


def add_roster_nav():
    st.sidebar.page_link("pages/12_Add_Roster.py", label="Add Roster", icon="➕")


def view_clips_nav():
    st.sidebar.page_link("pages/13_View_Clips.py", label="Clip Feed", icon="🎥")


# ---- Role: administrator ----------------------------------------------------

def admin_home_nav():
    st.sidebar.page_link("pages/20_Admin_Home.py", label="Admin Home", icon="🛠️")


def create_announcement_nav():
    st.sidebar.page_link(
        "pages/21_Create_Announcement.py", label="Create Announcement", icon="📣"
    )


# ---- Sidebar assembly -------------------------------------------------------

def SideBarLinks(show_home=False):
    """
    Renders sidebar navigation links based on the logged-in user's role.
    The role is stored in st.session_state when the user logs in on Home.py.
    """

    # Logo appears at the top of the sidebar on every page
    st.sidebar.image("assets/logo_white.png", width=150)

    # If no one is logged in, send them to the Home (login) page
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.switch_page("Home.py")

    if show_home:
        home_nav()

    if st.session_state["authenticated"]:

        if st.session_state["role"] == "athlete":
            athlete_home_nav()
            athlete_profile_nav()
            my_clips_nav()
            upload_clips_nav()

        if st.session_state["role"] == "recruiter":
            recruiter_home_nav()
            recruiter_profile_nav()
            add_roster_nav()
            view_clips_nav()

        if st.session_state["role"] == "administrator":
            admin_home_nav()
            create_announcement_nav()

    # About link appears at the bottom for all roles
    about_page_nav()

    if st.session_state["authenticated"]:
        if st.sidebar.button("Logout"):
            del st.session_state["role"]
            del st.session_state["authenticated"]
            st.switch_page("Home.py")
