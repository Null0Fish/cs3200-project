"""
The administrator's roster list (story 3.4).

A roster posting is what an athlete decides where to aim, so a false one is worth
finding: this lists every roster on the platform with the recruiter and
university behind it, the openings it advertises, and a delete button. Openings
can also be removed one at a time, for a roster that is real but advertises spots
that are not.
"""
import logging
logger = logging.getLogger(__name__)

import streamlit as st

from modules.api import delete_resource, fetch, full_name, show_flash
from modules.moderation import confirm_delete, require_admin
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()
require_admin()

st.title('Manage Rosters')
st.write('Every roster posting on the platform, with the account that posted it.')

show_flash()

sports = fetch('/sports')
if sports is None:
    st.stop()

sport_col, division_col, gender_col = st.columns(3)

with sport_col:
    sport_names = {sport['sport_id']: sport['name'] for sport in sports}
    sport_id = st.selectbox(
        'Sport',
        options=[None] + list(sport_names),
        format_func=lambda value: 'All sports' if value is None else sport_names[value],
    )

with division_col:
    division = st.text_input('Division').strip()

with gender_col:
    gender = st.selectbox(
        'Gender',
        options=[None, 'F', 'M'],
        format_func=lambda value: 'All' if value is None else value,
    )

# Only send the filters that were actually set; the API treats a missing
# parameter as "no filter" and an empty one the same way.
params = {}
if sport_id is not None:
    params['sport_id'] = sport_id
if division:
    params['division'] = division
if gender is not None:
    params['gender'] = gender

rosters = fetch('/roster', params=params)
if rosters is None:
    st.stop()

if not rosters:
    st.info('No rosters match those criteria.')
    st.stop()

# One request for every opening on the platform, grouped by roster here, rather
# than a request per roster in the loop below.
openings_by_roster = {}
for opening in fetch('/opening') or []:
    openings_by_roster.setdefault(opening['roster_id'], []).append(opening)

st.write(f'**{len(rosters)} rosters**')

st.dataframe(
    [
        {
            'ID': roster['roster_id'],
            'Team': roster['team_name'],
            'Sport': roster.get('sport_name') or '—',
            'Division': roster.get('division') or '—',
            'Gender': roster.get('gender') or '—',
            'Openings': roster['opening_count'],
            'Posted by': full_name(roster, prefix='recruiter_', fallback='—'),
            'University': roster.get('university_name') or '—',
        }
        for roster in rosters
    ],
    hide_index=True,
    use_container_width=True,
)

for roster in rosters:
    roster_id = roster['roster_id']
    recruiter_name = full_name(roster, prefix='recruiter_', fallback='an unknown account')

    st.divider()
    st.subheader(f"{roster['team_name']} — {roster.get('sport_name') or 'Unknown sport'}")
    st.caption(
        f"Roster #{roster_id} · posted by {recruiter_name} "
        f"(#{roster['recruiter_id']}) for {roster.get('university_name') or 'no university'} "
        f"· {roster['start_date']} to {roster['end_date']}"
    )

    # confirm_delete lays its two buttons out in columns, so the rows below stay
    # one level deep: Streamlit allows columns inside a column, but not deeper.
    openings = openings_by_roster.get(roster_id, [])
    if openings:
        st.write('**Openings**')
        for opening in openings:
            opening_number = opening['opening_number']
            text_col, delete_col = st.columns([3, 1])

            with text_col:
                st.write(
                    f"#{opening_number}: {opening.get('position') or 'Any position'} · "
                    f"GPA {opening.get('required_gpa') or 'any'} · "
                    f"height {opening.get('required_height_cm') or 'any'} cm · "
                    f"class of {opening.get('grad_year') or 'any'}"
                )

            with delete_col:
                if confirm_delete('Delete', key=f'opening_{roster_id}_{opening_number}'):
                    logger.info(
                        f'Admin deleting opening {opening_number} on roster {roster_id}'
                    )
                    delete_resource(
                        f'/roster/{roster_id}/opening/{opening_number}',
                        f'Deleted opening #{opening_number} on roster #{roster_id}.',
                    )
    else:
        st.caption('This roster advertises no openings.')

    account_col, delete_col = st.columns(2)

    with account_col:
        if st.button(f"View {recruiter_name}'s account", key=f'roster_account_{roster_id}',
                     use_container_width=True):
            st.session_state['selected_user_id'] = roster['recruiter_id']
            st.switch_page('pages/24_Account_Detail.py')

    with delete_col:
        if confirm_delete(
            'Delete Roster',
            key=f'roster_{roster_id}',
            warning=(
                f"Deleting this roster also deletes its {roster['opening_count']} "
                'opening(s) and every recorded view of it. This cannot be undone.'
            ),
        ):
            logger.info(f'Admin deleting roster {roster_id}')
            delete_resource(f'/roster/{roster_id}', f'Deleted roster #{roster_id}.')
