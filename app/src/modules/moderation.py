"""
Shared pieces of the administrator's moderation pages (persona 3, Jonathan).

Every moderation screen does the same two things around a delete: check that the
person doing it really is an administrator, and check that the click was
deliberate. Both live here so the pages themselves stay a description of what
they show.
"""
import streamlit as st


def require_admin():
    """
    Refuse to render the page for anyone who is not an administrator.

    SideBarLinks() bounces users who never logged in, but it does not check that
    the role matches the page — see docs/RBAC.md. These pages delete other
    people's accounts and content, so they check for themselves.
    """
    if st.session_state.get("role") != "administrator":
        st.error("You do not have access to this page.")
        st.stop()


def confirm_delete(label, key, warning="This cannot be undone."):
    """
    A delete button that takes two clicks, and returns True on the second.

    The first click parks a flag in session_state keyed by `key`, so each item in
    a list confirms independently and the rest of the page keeps working. Pass a
    key that identifies the row — "clip_7", not the row's position, which shifts
    as things get deleted.
    """
    pending_key = f"_confirm_{key}"

    if not st.session_state.get(pending_key):
        if st.button(label, key=f"_ask_{key}"):
            st.session_state[pending_key] = True
            st.rerun()
        return False

    st.warning(warning)
    confirm_col, cancel_col = st.columns(2)

    # Read the confirm button before handling cancel so both are rendered.
    confirmed = confirm_col.button("Yes, delete", key=f"_yes_{key}", type="primary")

    if cancel_col.button("Cancel", key=f"_no_{key}"):
        del st.session_state[pending_key]
        st.rerun()

    if confirmed:
        del st.session_state[pending_key]

    return confirmed
