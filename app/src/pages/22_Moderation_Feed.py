"""
The administrator's moderation feed (stories 3.1, 3.2, 3.5).

3.1 asks for an unfiltered feed "like a college recruiter" — the same clips the
recruiter's feed shows, in the same order, with nothing hidden — so that is what
loads by default and the athlete filter is only there to narrow it afterwards.
3.2 and 3.5 are the delete buttons under each clip and each comment.
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

st.title('Moderation Feed')
st.write(
    'Every clip on the platform, newest first, with the comments left on it. '
    'Nothing here is filtered out.'
)

show_flash()

clips = fetch('/clip')
if clips is None:
    st.stop()

if not clips:
    st.info('There are no clips on the platform.')
    st.stop()

# One request for the whole platform's comments, grouped by clip here, rather
# than a request per clip in the loop below.
comments = fetch('/comment') or []
comments_by_clip = {}
for comment in comments:
    comments_by_clip.setdefault(comment['clip_id'], []).append(comment)

# The feed is unfiltered by default; this narrows it to one athlete's clips once
# something in it has caught the admin's eye.
athlete_names = {
    clip['athlete_id']: full_name(clip) for clip in clips
}
athlete_choice = st.selectbox(
    'Show clips by',
    options=[None] + sorted(athlete_names, key=lambda user_id: athlete_names[user_id]),
    format_func=lambda user_id: (
        'Everyone' if user_id is None else f'{athlete_names[user_id]} (#{user_id})'
    ),
)
if athlete_choice is not None:
    clips = [clip for clip in clips if clip['athlete_id'] == athlete_choice]

st.write(f'**{len(clips)} clips**')

for clip in clips:
    clip_id = clip['clip_id']
    poster = full_name(clip)
    clip_comments = comments_by_clip.get(clip_id, [])

    st.divider()
    st.subheader(clip['caption'])
    st.caption(
        f"Clip #{clip_id} · posted by {poster} (#{clip['athlete_id']}) "
        f"on {clip['posted_at']} · {clip['comment_count']} comment(s)"
    )

    video_col, actions_col = st.columns([3, 2])

    with video_col:
        render_clip_video(clip)

    with actions_col:
        if st.button(f"View {poster}'s account", key=f'account_{clip_id}',
                     use_container_width=True):
            st.session_state['selected_user_id'] = clip['athlete_id']
            st.switch_page('pages/24_Account_Detail.py')

        # Story 3.2 - take a clip down for a content violation. Its comments go
        # with it, which is why the confirmation says how many.
        if confirm_delete(
            'Delete Clip',
            key=f'clip_{clip_id}',
            warning=(
                f'Deleting this clip also deletes its {len(clip_comments)} '
                f'comment(s). This cannot be undone.'
            ),
        ):
            logger.info(f'Admin deleting clip {clip_id}')
            delete_resource(f'/clip/{clip_id}', f'Deleted clip #{clip_id}.')

    # Story 3.5 - delete a comment without touching the clip it sits under.
    if clip_comments:
        with st.expander(f'Comments ({len(clip_comments)})'):
            for comment in clip_comments:
                comment_id = comment['comment_id']
                text_col, delete_col = st.columns([4, 1])

                with text_col:
                    st.write(comment['content'])
                    st.caption(
                        f"{full_name(comment)} on {comment['posted_at']} "
                        f"· comment #{comment_id}"
                    )

                with delete_col:
                    if confirm_delete('Delete', key=f'comment_{comment_id}'):
                        logger.info(f'Admin deleting comment {comment_id}')
                        delete_resource(
                            f'/comment/{comment_id}',
                            f'Deleted comment #{comment_id}.',
                        )
    else:
        st.caption('No comments on this clip.')
