"""
Thin wrapper around the calls every page makes to the Flask API.

Pages talk to the API over the Docker network, so the base URL is the web-api
hostname rather than localhost — the browser never sees it. The one exception is
a clip's video file, which the browser fetches itself; see modules/clips.py.

The helpers here exist because a page that reads a resource, deletes another, and
reports what happened is otherwise three-quarters request plumbing. fetch() and
delete_resource() both surface their own failures with st.error, so a caller only
has to handle the success case (fetch returns None when the request failed).
"""
import logging

import requests
import streamlit as st

logger = logging.getLogger(__name__)

API_BASE_URL = "http://web-api:4000/talent_scout"

# The key a flash message is parked under between a rerun and the next render.
_FLASH_KEY = "_flash_message"


def api_error(response):
    """The error message from a failed API response, in a form safe to display."""
    try:
        return response.json().get("error", "Unknown error")
    except ValueError:
        # A 500 from Flask's own error handler is an HTML page, not JSON.
        return response.reason or "Unknown error"


def full_name(record, prefix="", fallback="Deleted user"):
    """
    A display name from the first_name/last_name pair an API record carries.

    Records that reach user through a nullable column come back with both names
    NULL — a comment whose author has since been deleted, for instance — hence
    the fallback. Pass prefix for the joined-in names that carry one, such as
    recruiter_first_name on a roster.
    """
    parts = [record.get(f"{prefix}first_name"), record.get(f"{prefix}last_name")]
    return " ".join(part for part in parts if part) or fallback


def fetch(path, params=None):
    """
    GET API_BASE_URL + path and return the parsed body, or None on any failure.

    The failure is reported to the user here, so callers only branch on None to
    decide whether they have anything to render.
    """
    try:
        response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        logger.error(f'GET {path} failed: {e}')
        st.error(f"Error connecting to the API: {e}")
        st.info("Please ensure the API server is running")
        return None

    if response.status_code != 200:
        st.error(f"Request failed: {api_error(response)}")
        return None

    return response.json()


def flash(message, kind="success"):
    """
    Queue a message to show after the next rerun.

    Anything written with st.success right before st.rerun() is wiped by the
    rerun, which is exactly the situation after a successful delete. Parking the
    message in session_state carries it across.
    """
    st.session_state[_FLASH_KEY] = (kind, message)


def show_flash():
    """Display and clear the queued message, if there is one."""
    queued = st.session_state.pop(_FLASH_KEY, None)
    if queued:
        kind, message = queued
        getattr(st, kind)(message)


def delete_resource(path, success_message, rerun=True):
    """
    DELETE API_BASE_URL + path, returning True if the row is gone.

    success_message is queued with flash() either way, so it survives whatever
    the caller does next. By default the page then reruns — the list the deleted
    row came from is now stale — and this does not return at all. Pass
    rerun=False when the page itself is about the deleted row and the caller
    needs to navigate away instead of re-rendering.
    """
    try:
        response = requests.delete(f"{API_BASE_URL}{path}", timeout=10)
    except requests.exceptions.RequestException as e:
        logger.error(f'DELETE {path} failed: {e}')
        st.error(f"Error connecting to the API: {e}")
        return False

    if response.status_code == 200:
        logger.info(f'DELETE {path} succeeded')
        flash(success_message)
        if rerun:
            st.rerun()
        return True

    st.error(f"Delete failed: {api_error(response)}")
    return False
