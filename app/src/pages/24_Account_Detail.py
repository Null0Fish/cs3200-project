"""
The administrator's view of one account (stories 3.3, 3.4).

An account means different things depending on what it is: an athlete has
metrics, personal records and clips, a recruiter has a university and roster
postings, and neither view makes sense for the other. So the page reads the role
the API derived for the account and renders that role's view, with the content
the account owns deletable in place and the account itself deletable at the
bottom.

Reached from the account list and the moderation feed, both of which set
selected_user_id, so it has no sidebar link of its own.
"""
import logging
logger = logging.getLogger(__name__)

import streamlit as st

from modules.api import delete_resource, fetch, full_name, show_flash
from modules.clips import render_clip_video
from modules.moderation import confirm_delete, require_admin
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()
require_admin()

st.title('Account Detail')

selected_user_id = st.session_state.get('selected_user_id')

if selected_user_id is None:
    st.error('No account selected.')
    if st.button('Back to Accounts'):
        st.switch_page('pages/23_Manage_Accounts.py')
    st.stop()

show_flash()

user = fetch(f'/user/{selected_user_id}')
if user is None:
    if st.button('Back to Accounts'):
        st.switch_page('pages/23_Manage_Accounts.py')
    st.stop()

st.header(full_name(user, fallback='Unnamed account'))
st.caption(f"Account #{user['user_id']} · {user['role']}")

contact_col, content_col = st.columns(2)

with contact_col:
    st.subheader('Contact')
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Phone:** {user.get('phone') or 'N/A'}")

with content_col:
    st.subheader('Content on the platform')
    clip_metric, comment_metric, roster_metric = st.columns(3)
    clip_metric.metric('Clips', user['clip_count'])
    comment_metric.metric('Comments', user['comment_count'])
    roster_metric.metric('Rosters', user['roster_count'])


# ---- The athlete view -------------------------------------------------------

def render_athlete_view(user_id):
    """Metrics, personal record history, and the clips this athlete posted."""
    athlete = fetch(f'/athlete/{user_id}')
    if athlete is None:
        return

    st.subheader('Athlete Profile')
    left, right = st.columns(2)
    with left:
        st.write(f"**GPA:** {float(athlete['gpa']):.2f}")
        st.write(f"**Graduation year:** {athlete['graduation_year']}")
        st.write(f"**Date of birth:** {athlete['dob']}")
    with right:
        st.write(f"**Height:** {athlete['height_cm']} cm")
        st.write(f"**Weight:** {athlete['weight_kg']} kg")
        st.write(f"**Status:** {athlete.get('recruitment_status') or 'N/A'}")

    st.subheader('Personal Records')
    records = athlete.get('personal_records', [])
    if records:
        st.dataframe(
            [
                {
                    'Event': record['event'],
                    'Date': record['date'],
                    'Time': record.get('time') or '—',
                    'Score': record.get('score') if record.get('score') is not None else '—',
                }
                for record in records
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info('This athlete has no personal records.')

    # Story 3.2 from the account side: the same clip deletes as the moderation
    # feed, narrowed to one athlete's posts.
    st.subheader('Clips')
    clips = athlete.get('clips', [])
    if not clips:
        st.info('This athlete has not posted any clips.')
        return

    for clip in clips:
        clip_id = clip['clip_id']
        with st.expander(f"{clip['caption']} — posted {clip['posted_at']}"):
            render_clip_video(clip)
            if confirm_delete('Delete Clip', key=f'detail_clip_{clip_id}'):
                logger.info(f'Admin deleting clip {clip_id}')
                delete_resource(f'/clip/{clip_id}', f'Deleted clip #{clip_id}.')


# ---- The recruiter view -----------------------------------------------------

def render_recruiter_view(user_id):
    """The university this recruiter posts for, and the rosters they posted."""
    recruiter = fetch(f'/recruiter/{user_id}')
    if recruiter is None:
        return

    university = recruiter.get('university', {})
    st.subheader('University')
    st.write(f"**Name:** {university.get('name', 'N/A')}")
    st.write(f"**Website:** {university.get('website_url') or 'N/A'}")

    # Story 3.4 - a false roster is deleted from whichever account posted it.
    st.subheader('Roster Postings')
    rosters = recruiter.get('rosters', [])
    if not rosters:
        st.info('This recruiter has not posted any rosters.')
        return

    for roster in rosters:
        roster_id = roster['roster_id']
        with st.expander(
            f"{roster['team_name']} — {roster.get('sport_name') or 'Unknown sport'}"
        ):
            st.write(f"**Division:** {roster.get('division') or 'N/A'}")
            st.write(f"**Gender:** {roster.get('gender') or 'N/A'}")
            st.write(f"**Season:** {roster['start_date']} to {roster['end_date']}")

            if confirm_delete(
                'Delete Roster',
                key=f'detail_roster_{roster_id}',
                warning='The openings on this roster are deleted with it. This cannot be undone.',
            ):
                logger.info(f'Admin deleting roster {roster_id}')
                delete_resource(f'/roster/{roster_id}', f'Deleted roster #{roster_id}.')


# ---- Role dispatch ----------------------------------------------------------

if user['role'] == 'athlete':
    render_athlete_view(selected_user_id)
elif user['role'] == 'recruiter':
    render_recruiter_view(selected_user_id)
elif user['role'] == 'administrator':
    st.info(
        'This is an administrator account. Administrators moderate content and '
        'post platform announcements; they have no profile of their own.'
    )
elif user['role'] == 'analyst':
    st.info(
        'This is a data analyst account. Analysts only read aggregate, '
        'de-identified data, so there is no profile content attached to it.'
    )
else:
    st.warning(
        'This user row belongs to no role. It can still be deleted, but there '
        'is nothing else to show.'
    )


# ---- Deleting the account itself (3.3, 3.4) ---------------------------------

st.divider()
st.subheader('Delete Account')

if selected_user_id == st.session_state.get('user_id'):
    st.info('This is the account you are logged in as, so it cannot be deleted here.')
else:
    st.write(
        f"Deleting this account also deletes its {user['clip_count']} clip(s), "
        f"{user['comment_count']} comment(s) and {user['roster_count']} roster(s), "
        'along with every recorded view of or by it.'
    )
    if confirm_delete(
        f"Delete {full_name(user, fallback='this account')}'s Account",
        key=f"account_{user['user_id']}",
        warning='The account and all of its content are removed. This cannot be undone.',
    ):
        logger.info(f"Admin deleting account {user['user_id']}")
        # Deleting the user row is what cascades; /user takes any role, so this
        # one call covers athletes, recruiters, admins and analysts alike.
        # Rerunning would reload a page about an account that no longer exists,
        # so on success go back to the list instead.
        deleted = delete_resource(
            f"/user/{user['user_id']}",
            f"Deleted the account of {full_name(user, fallback='an unnamed user')}.",
            rerun=False,
        )
        if deleted:
            del st.session_state['selected_user_id']
            st.switch_page('pages/23_Manage_Accounts.py')

st.divider()
if st.button('Back to Accounts'):
    st.switch_page('pages/23_Manage_Accounts.py')
