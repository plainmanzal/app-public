# Written by Eni Mustafaraj

import streamlit as st
import requests

@st.cache_data(ttl=3600)
def get_user_info(access_token):
    """Fetch and cache user profile info from Google."""
    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.warning(f"User info fetch failed: {e}")
    return None


def render_user_profile():
    """Render user profile photo and a greeting, if user opts in."""
    access_token = st.session_state.get("access_token")
    if not access_token:
        return

    show_profile = st.sidebar.checkbox("Show profile info", value=True)

    if show_profile:
        user = get_user_info(access_token)
        if user:
            first_name = user.get("given_name") or user.get("name", "there").split()[0]
            col1, col2 = st.sidebar.columns([1, 4])
            with col1:
                st.image(user.get("picture"), width=40)
            with col2:
                st.markdown(f"**Hello, {first_name}!**")
        else:
            st.sidebar.success("Logged in ✅")
    else:
        st.sidebar.success("Logged in ✅")



# VERSION that I'm using for DEBUGGING
def render_user_profile():
    """Render user profile photo and greeting, if user opts in."""
    access_token = st.session_state.get("access_token")
    if not access_token:
        return

    show_profile = st.sidebar.checkbox("Show profile info", value=True)

    if show_profile:
        if "fake_user_name" in st.session_state:
            first_name = st.session_state["fake_user_name"]
            picture = st.session_state["fake_user_picture"]
        else:
            user = get_user_info(access_token)
            if not user:
                st.sidebar.success("Logged in ✅")
                return
            first_name = user.get("given_name") or user.get("name", "there").split()[0]
            picture = user.get("picture")

        col1, col2 = st.sidebar.columns([1, 4])
        with col1:
            st.image(picture, width=40)
        with col2:
            st.markdown(f"**Hello, {first_name}!**")
    else:
        st.sidebar.success("Logged in ✅")
        
    conn = create_user_connection(USER_DB)
    cursor = conn.cursor()
    user_id = st.session_state["user_id"]
    cursor.execute("SELECT goal, food_preferences FROM User WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    current_goal = row[0] if row else ""
    current_prefs = row[1] if row else ""

    with st.form("profile_form"):
        calorie_goal = st.number_input("Calorie Goal", min_value=0, value=int(current_goal) if current_goal else 2000)
        preferences = st.text_input("Food Preferences (comma-separated)", value=current_prefs or "")
        submitted = st.form_submit_button("Save Preferences")
        if submitted:
            cursor.execute(
                "UPDATE User SET goal = ?, food_preferences = ? WHERE user_id = ?",
                (calorie_goal, preferences, user_id)
            )
            conn.commit()
            st.success("Preferences updated!")
    cursor.close()
    conn.close()