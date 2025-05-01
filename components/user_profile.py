# Written by Eni Mustafaraj

import streamlit as st
import requests
import sqlite3
from database.user_db import create_connection as create_user_connection, USER_DB
from database.menu_db import create_connection, WFR_DB

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




# ... other imports ...
from database.user_db import create_connection as create_user_connection, USER_DB
from database.menu_db import create_connection as create_menu_connection, WFR_DB # Corrected import

# ... existing functions ...

def render_profile_form(user_id):
    # --- Bitzy CSS (Keep existing CSS, ensure .stTextInput label is styled if needed) ---
    st.markdown("""
    <style>
    /* ... Keep all your existing styles ... */
    .bitzy-container {
        background: #fff6fb;
        border-radius: 18px;
        box-shadow: 0 2px 16px #ffd4f1;
        padding: 2em 2em 1.5em 2em;
        margin: 0 auto 2em auto;
        max-width: 700px;
        font-family: 'Quicksand', 'Montserrat', sans-serif;
    }
    .bitzy-header {
        font-size: 1.3rem; /* Adjusted for consistency */
        font-weight: bold;
        color: #ffffff;
        background-color: #ff96ec;
        padding: 0.5em 1em;
        border-radius: 16px;
        margin: 0 0 1.5em 0; /* Adjusted margin */
        text-align: center;
        font-family: 'Quicksand', 'Montserrat', sans-serif;
        box-shadow: 0 0 8px 2px #ff96ec;
    }
    .bitzy-subtitle {
        font-size: 1.2rem;
        font-weight: bold;
        color: #ff96ec;
        margin-bottom: 0.5em;
        font-family: 'Quicksand', 'Montserrat', sans-serif;
        text-align: center;
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0 0 8px 2px #ff96ec;
        padding: 0.3em 0.5em; /* Added padding */
    }
    .bitzy-flex-row {
        display: flex;
        gap: 2em;
        justify-content: space-between;
        margin-bottom: 1.5em; /* Added margin */
    }
    .bitzy-col {
        flex: 1 1 0;
        min-width: 0;
        display: flex;
        flex-direction: column;

    }

    /* Ensure input labels are styled */
     .stTextInput label, .stNumberInput label {
        font-weight: bold !important;
        color: #272936 !important; /* Ensure readability */
     }
    </style>
    """, unsafe_allow_html=True)

    conn_user = create_user_connection(USER_DB)
    conn_wfr = create_menu_connection(WFR_DB) # Use correct function
    cursor_user = conn_user.cursor()
    cursor_wfr = conn_wfr.cursor()

    # Fetch user preferences AND username from USER_DB
    cursor_user.execute("SELECT username, goal, food_preferences, allergens FROM User WHERE user_id = ?", (user_id,))
    row = cursor_user.fetchone()
    current_username = row[0] if row else "User"
    current_goal = row[1] if row else ""
    current_prefs_str = row[2] if row else ""
    current_allergens_str = row[3] if row else ""
    current_prefs = set(current_prefs_str.split(",") if current_prefs_str else [])
    current_allergens = set(current_allergens_str.split(",") if current_allergens_str else [])


    # Fetch options from WFR_DB
    cursor_wfr.execute("SELECT DISTINCT preferences FROM Dish")
    food_options = set(p.strip() for row in cursor_wfr.fetchall() for p in (row[0] or "").split(",") if p.strip())

    cursor_wfr.execute("SELECT DISTINCT allergens FROM Dish")
    allergen_options = set(a.strip() for row in cursor_wfr.fetchall() for a in (row[0] or "").split(",") if a.strip())


    with st.form("profile_form", clear_on_submit=False):
        st.markdown("<div class='bitzy-header'>⚙️ Settings & Preferences</div>", unsafe_allow_html=True)

        # --- Username Input ---
        new_username = st.text_input("Username", value=current_username)
        if new_username.strip() == "":
            st.warning("Username cannot be empty. Please enter a valid username.")
        elif new_username != current_username:
            cursor_user.execute("SELECT COUNT(*) FROM User WHERE username = ?", (new_username,))
            if cursor_user.fetchone()[0] > 0:
                st.warning("This username is already taken. Please choose a different one.")

        # --- Calorie Goal ---
        calorie_goal = st.number_input("Calorie Goal", min_value=0, value=int(current_goal) if current_goal else 2000)

        # Validate and update calorie goal if changed
        if calorie_goal != (int(current_goal) if current_goal else 2000):
            cursor_user.execute(
            "UPDATE User SET goal = ? WHERE user_id = ?",
            (calorie_goal, user_id)
            )
            conn_user.commit()

        # --- Preferences and Allergens in Columns ---


        # Preferences column
        st.markdown("<div class='bitzy-subtitle'>Preferences</div>", unsafe_allow_html=True)
        selected_prefs = set()
        for option in sorted(list(food_options)):
             is_checked = st.checkbox(option, value=(option in current_prefs), key=f"pref_{option}")
             if is_checked:
                 selected_prefs.add(option)
        st.markdown('</div>', unsafe_allow_html=True) # Close checkbox-group
        st.markdown('</div>', unsafe_allow_html=True) # Close col

        # Allergens column
        st.markdown("<div class='bitzy-subtitle'>Allergens</div>", unsafe_allow_html=True)
        selected_allergens = set()
        for option in sorted(list(allergen_options)):
             is_checked = st.checkbox(option, value=(option in current_allergens), key=f"allergen_{option}")
             if is_checked:
                 selected_allergens.add(option)
        st.markdown('</div>', unsafe_allow_html=True) # Close checkbox-group
        st.markdown('</div>', unsafe_allow_html=True) # Close col

        st.markdown('</div>', unsafe_allow_html=True)  # Close flex row

        # --- Submit Button ---
        submitted = st.form_submit_button(
            "Save Changes",
            use_container_width=True,
            help="Click to save your changes"
        )

        if submitted:
            try:
                # Prepare data for update
                prefs_to_save = ",".join(sorted(list(selected_prefs)))
                allergens_to_save = ",".join(sorted(list(selected_allergens)))

                # Update User table
                cursor_user.execute(
                    """UPDATE User
                       SET username = ?, goal = ?, food_preferences = ?, allergens = ?
                       WHERE user_id = ?""",
                    (new_username, str(calorie_goal), prefs_to_save, allergens_to_save, user_id)
                )
                conn_user.commit()
                st.success("Changes were saved! ✨")
                # Update session state if username changed
                if new_username != current_username:
                    st.session_state['db_username'] = new_username # Store db username
                st.rerun() # Rerun to reflect changes immediately
            except sqlite3.Error as e:
                st.error(f"Database error: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

    st.markdown('</div>', unsafe_allow_html=True)  # Close bitzy-container

    # Close connections
    cursor_user.close()
    conn_user.close()
    cursor_wfr.close()
    conn_wfr.close()