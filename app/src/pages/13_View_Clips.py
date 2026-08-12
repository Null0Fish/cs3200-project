import logging
logger = logging.getLogger(__name__)

import requests
import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title("Clips")

# API endpoints
API_BASE_URL = "http://web-api:4000/talent_scout"

try:
    response = requests.get(f"{API_BASE_URL}/clip")
    response.raise_for_status()
    
    clips = response.json()
    
    if not clips:
        st.info("No clips available")
    else:
        st.dataframe(clips)
        
except Exception as e:
    st.error(f"Error loading clips: {str(e)}")
    st.info("Please ensure the API server is running")
