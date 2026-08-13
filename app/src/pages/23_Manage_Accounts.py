"""
The administrator's account list (stories 3.3, 3.4).

Both stories start the same way — "view and delete" — so this page is the view
half for every account on the platform, and the account detail page it opens is
where the role-specific view and the delete button live.
"""
import logging
logger = logging.getLogger(__name__)

import streamlit as st

from modules.api import fetch, full_name, show_flash
from modules.moderation import require_admin
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()
require_admin()

st.title('Manage Accounts')
st.write('Every account on the platform. Open one to see its content and delete it.')

show_flash()

# 'unassigned' is not a filter the API accepts: it is the CASE fallback for a
# user row with no subtype, so those accounts only show up under "All".
ROLE_FILTERS = ['All', 'athlete', 'recruiter', 'administrator', 'analyst']

filter_col, search_col = st.columns([1, 2])

with filter_col:
    role = st.selectbox('Role', ROLE_FILTERS)

with search_col:
    search = st.text_input('Search by name or email').strip().lower()

users = fetch('/user', params=None if role == 'All' else {'role': role})
if users is None:
    st.stop()

if search:
    users = [
        user for user in users
        if search in full_name(user).lower() or search in user['email'].lower()
    ]

if not users:
    st.info('No accounts match those criteria.')
    st.stop()

st.write(f'**{len(users)} accounts**')

st.dataframe(
    [
        {
            'ID': user['user_id'],
            'Name': full_name(user),
            'Role': user['role'],
            'Email': user['email'],
            'Phone': user.get('phone') or '—',
        }
        for user in users
    ],
    hide_index=True,
    use_container_width=True,
)

st.subheader('Open an account')

for user in users:
    user_id = user['user_id']
    label_col, button_col = st.columns([3, 1])

    with label_col:
        st.write(f"**{full_name(user)}** · {user['role']} · #{user_id}")

    with button_col:
        if st.button('View', key=f'view_user_{user_id}', use_container_width=True):
            st.session_state['selected_user_id'] = user_id
            st.switch_page('pages/24_Account_Detail.py')
