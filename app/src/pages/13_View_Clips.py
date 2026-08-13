"""
The recruiter's clip feed (story 2.1).

Every clip on the platform, newest first. A clip whose clip_url is set plays
here; one without a video file attached shows its caption and comments only.
"""
import logging
logger = logging.getLogger(__name__)

import streamlit as st

from modules.api import fetch, full_name
from modules.clips import render_clip_video
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

# Show appropriate sidebar links for the role of the currently logged in user
SideBarLinks()

st.title('Clip Feed')

clips = fetch('/clip')
if clips is None:
    st.stop()

if not clips:
    st.info('No clips available')
    st.stop()

# One request for every comment on the platform, grouped by clip here, rather
# than a request per clip in the loop below.
comments_by_clip = {}
for comment in fetch('/comment') or []:
    comments_by_clip.setdefault(comment['clip_id'], []).append(comment)

st.write(f'**{len(clips)} clips**')

for clip in clips:
    clip_id = clip['clip_id']
    clip_comments = comments_by_clip.get(clip_id, [])

    st.divider()
    st.subheader(clip['caption'])
    st.caption(f"{full_name(clip)} · posted {clip['posted_at']}")

    render_clip_video(clip)

    if clip_comments:
        with st.expander(f'Comments ({len(clip_comments)})'):
            for comment in clip_comments:
                st.write(comment['content'])
                st.caption(f"{full_name(comment)} on {comment['posted_at']}")
