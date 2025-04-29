import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
from components.menu_display import display_menu_and_handle_journal
from database.user_db import create_connection as create_user_connection, add_user, USER_DB, display_journal, display_user_dish_ratings
from .user_profile import render_profile_form
from temp_graph_stuff import create_plots
import sqlite3


DEBUG = False # keep False when testing Google Login
# Code written by Eni Mustafaraj

def fake_login():
    """Sets a fake access token and user info for debugging."""
    st.session_state["access_token"] = "fake-token"
    st.session_state["fake_user_name"] = "Test Student"
    st.session_state["fake_user_picture"] = "https://i.pravatar.cc/60?img=25"  # random placeholder

def handle_logout():
    if st.sidebar.button("Logout"):
        st.session_state.clear()  # Clear all session state variables
        st.rerun()


import requests

import streamlit as st
import requests

def google_login():
    """Manual OAuth login with a working Google Auth URL."""
    CLIENT_ID = st.secrets["google"]["client_id"]
    REDIRECT_URI = st.secrets["google"]["redirect_uri"]
    SCOPE = "openid email profile"
    AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

    params = st.query_params

    # Step 1: Handle callback
    if "code" in params and "state" in params and "access_token" not in st.session_state:
        code = params["code"]

        try:
            response = requests.post(
                TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": CLIENT_ID,
                    "client_secret": st.secrets["google"]["client_secret"],
                    "redirect_uri": REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            response.raise_for_status()
            token = response.json()
            st.session_state["access_token"] = token["access_token"]
            st.query_params.clear()
            return True
        except Exception as e:
            st.error(f"Login failed: {e}")
            st.query_params.clear()
            return False

    # Step 2: Show login button with working link
    if "access_token" not in st.session_state:
        auth_url = (
            f"{AUTH_ENDPOINT}?"
            f"client_id={CLIENT_ID}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"response_type=code&"
            f"scope={SCOPE.replace(' ', '%20')}&"
            f"access_type=offline&"
            f"prompt=consent&"
            f"state=streamlit_login"
        )

        #st.write(auth_url)
        st.sidebar.link_button("🔐 Login with Google", url=auth_url)
        return False

    return True


def render_location(connection):
            
        # Navigation
        selected_tab = st.sidebar.radio("Navigate", ["Home", "Menu",  "Food Journal", "Profile"])
        st.session_state["selected_tab"] = selected_tab
            
        if selected_tab == "Profile":
            st.sidebar.markdown("---")
            st.markdown(
            """
            <div style="
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            box-shadow: 0 0 12px 3px rgba(255, 255, 255, 0.3), 0 0 24px 6px rgba(255, 255, 255, 0.3);
            padding: 10px;
            margin-bottom: 20px;
            text-align: center;
            ">
            <h1 style='color:#ff96ec;'>Profile</h1>
            </div>
            """,
            unsafe_allow_html=True,
            )
            
            render_profile_form(st.session_state.user_id)

        elif selected_tab == "Food Journal":
            st.sidebar.markdown("---")
            st.markdown(
            """
            <div style="
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            box-shadow: 0 0 12px 3px rgba(255, 255, 255, 0.3), 0 0 24px 6px rgba(255, 255, 255, 0.3);
            padding: 10px;
            text-align: center;
            margin-bottom: 20px;
            ">
            <h1 style='color:#ff96ec;'>Food Journal</h1>
            </div>
            """,
            unsafe_allow_html=True,
            )

            create_plots()
            display_journal(connection, st.session_state.user_id)

        elif selected_tab == "Menu":
            st.sidebar.markdown("---")
            st.markdown(
            """
            <div style="
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            box-shadow: 0 0 12px 3px rgba(255, 255, 255, 0.3), 0 0 24px 6px rgba(255, 255, 255, 0.3);
            padding: 10px;
            margin-bottom: 20px;
            text-align: center;
            ">
            <h1 style='color:#ff96ec;'>Menu</h1>
            </div>
            """,
            unsafe_allow_html=True,
            )

            display_menu_and_handle_journal(connection)

            # Close the div
            st.markdown("</div>", unsafe_allow_html=True)
          
    



def render_sidebar():
    """Handles the login/logout process and user info in the sidebar."""
    st.sidebar.markdown(
        """
        <div style="
            background-color: white;
            border-radius: 15px;
            box-shadow: 0 0 24px 6px rgba(255, 150, 236, 0.5), 0 0 48px 12px rgba(255, 212, 241, 0.5);
            padding: 10px;
            margin-bottom: 20px;
            text-align: center;
        ">
            <h1 style='color:#ff96ec; font-family:Quicksand,Montserrat,sans-serif;'>Byte By Bite</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    logged_in = google_login()

    if logged_in:
        user_id = st.session_state.get("user_id")
        db_username = st.session_state.get("db_username")
        user_picture = st.session_state.get("user", {}).get("picture")

        # Fetch user info from DB if not already in session state or needs update
        if user_id and not db_username:
            conn = None
            try:
                conn = create_user_connection(USER_DB)
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM User WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                if result:
                    st.session_state["db_username"] = result[0]
                    db_username = result[0]
            except sqlite3.Error as e:
                 st.sidebar.warning(f"DB Error: {e}")
            finally:
                if conn:
                    conn.close()

        # Fetch Google info if needed (only on first login after token)
        if "user" not in st.session_state and "access_token" in st.session_state:
             try:
                oauth = OAuth2Session(token={"access_token": st.session_state["access_token"]})
                user_info = oauth.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
                st.session_state["user"] = { # Store Google info separately if needed
                    "name": user_info.get("name"),
                    "email": user_info.get("email"),
                    "picture": user_info.get("picture"),
                }
                user_picture = user_info.get("picture") # Update picture

                # --- Database Check/Add User on First Login ---
                conn = None
                try:
                    conn = create_user_connection(USER_DB)
                    cursor = conn.cursor()
                    email = user_info.get("email")
                    google_name = user_info.get("name") # Use Google name as default username

                    cursor.execute("SELECT user_id, username FROM User WHERE email = ?", (email,))
                    row = cursor.fetchone()
                    if row:
                        st.session_state["user_id"] = row[0]
                        st.session_state["db_username"] = row[1] # Store db username
                        st.session_state["welcome_status"] = "back"
                        user_id = row[0]
                        db_username = row[1]
                    else:
                        # Add user with Google name as initial username
                        new_user_id = add_user(conn, google_name, email)
                        if new_user_id:
                             st.session_state["user_id"] = new_user_id
                             st.session_state["db_username"] = google_name # Store db username
                             st.session_state["welcome_status"] = "new"
                             user_id = new_user_id
                             db_username = google_name
                        else:
                             st.sidebar.error("Failed to add user to database.")
                             logged_in = False # Treat as not logged in if DB add fails
                except sqlite3.Error as e:
                     st.sidebar.error(f"Database connection/query failed: {e}")
                     logged_in = False # Treat as not logged in on DB error
                finally:
                    if conn:
                        conn.close()
             except Exception as e:
                  st.sidebar.error(f"Failed to fetch Google user info: {e}")
                  logged_in = False # Treat as not logged in if Google fetch fails


        # Display user info if successfully logged in and user_id is set
        if logged_in and user_id:
            display_name = db_username or "User" # Use DB username, fallback to "User"
            welcome_status = st.session_state.get("welcome_status", "back")
            welcome_message = (
                f"""
                <div style="
                    background-color: rgba(255, 255, 255, 0.0);
                    border: 2px solid #ff96ec;
                    border-radius: 15px;
                    box-shadow: 0 0 12px 3px rgba(255, 150, 236, 0.5), 0 0 24px 6px rgba(255, 150, 236, 0.3);
                    padding: 10px;
                    text-align: center;
                    color: #272936;
                    font-weight: bold;
                    font-size: 1.1em;
                ">
                    <span style='color:#ff96ec;'>Bitzy</span> says Welcome back, {display_name}!~
                </div>
                """
                if welcome_status == "back"
                else f"""
                <div style="
                    background-color: rgba(255, 255, 255, 0.0);
                    border: 2px solid #ff96ec;
                    border-radius: 15px;
                    box-shadow: 0 0 12px 3px rgba(255, 150, 236, 0.5), 0 0 24px 6px rgba(255, 150, 236, 0.3);
                    padding: 10px;
                    text-align: center;
                    color: #272936;
                    font-weight: bold;
                    font-size: 1.1em;
                ">
                    <span style='color:#ff96ec;'>Bitzy</span> says Welcome, {display_name}!~
                </div>
                """
            )
            st.sidebar.markdown(
                f"""
                <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 10px;">
                <img src="{user_picture or 'https://i.imgur.com/TMVgTr0.png'}" style="width: 60px; height: 60px; border: 3px solid #ff96ec; border-radius: 50%;">
                </div>
                <div style="text-align: center; color: #272936; font-weight: bold; font-size: 1.1em;">
                 {welcome_message}
                </div>
                """,
                unsafe_allow_html=True,
            )
            handle_logout()
