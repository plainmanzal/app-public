import streamlit as st
from components.auth import render_sidebar
from datetime import timedelta, date
from components.menu_display import display_menu_and_handle_journal
from components.auth import render_location
from database.user_db import create_connection as create_user_connection, USER_DB
from database.menu_db import create_wfr_tables, update_all_menus_for_week

from database.menu_db import create_connection, WFR_DB, update_all_menus_for_week
import os

create_wfr_tables()

today = date.today()
monday = today - timedelta(days=today.weekday())
monday_str = monday.strftime('%Y-%m-%d')

# --- Only update menus once per week for all users (using a file flag) ---
def menu_update_needed(monday_str):
    flag_file = f".menu_updated_{monday_str}"
    return not os.path.exists(flag_file)

def set_menu_updated(monday_str):
    flag_file = f".menu_updated_{monday_str}"
    with open(flag_file, "w") as f:
        f.write("updated")

if menu_update_needed(monday_str):
    conn_wfr = create_connection(WFR_DB)
    with st.spinner(f"Updating menus for the week of {monday_str}..."):
        update_all_menus_for_week(monday_str, conn_wfr)
    conn_wfr.close()
    set_menu_updated(monday_str)
    st.success("Menus updated for this week!")

# --- Google Fonts for extra polish ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@700;900&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

if "user_id" not in st.session_state:
    st.markdown(
        """
        <style>
        .welcome-box {
            background: #fff;
            border-radius: 24px;
            padding: 3em;
            box-shadow: 0 0 24px 6px rgba(255, 150, 236, 0.5), 0 0 48px 12px rgba(255, 212, 241, 0.5);
            max-width: 800px;
            margin: auto;
            font-size: 1.8rem;
            line-height: 1.6;
            color: #272936;
            font-family: 'Quicksand', 'Montserrat', 'sans-serif';
            text-align: center;
        }
        .welcome-box b {
            font-size: 2.2rem;
            color: #ff96ec;
        }
        .bitzy-logo {
            width: 100px;
            margin-bottom: 1em;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

if "selected_tab" not in st.session_state:
    st.session_state["selected_tab"] = "Home"

# --- Custom CSS for branding, overlays, and buttons ---
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-family: 'Quicksand', 'Montserrat', 'sans-serif' !important;
    }
    .main-title {
        font-size: 4rem;
        color: #ff96ec;
        font-family: 'Quicksand', 'Montserrat', 'sans-serif';
        text-align: center;
        margin-bottom: 0.2em;
        letter-spacing: 2px;
        font-weight: 900;
        text-shadow: 2px 2px 0 #ffd4f1;
    }
    .subtitle {
        font-size: 1.3rem;
        color: #272936;
        text-align: center;
        margin-bottom: 1.5em;
        font-family: 'Quicksand', 'Montserrat', 'sans-serif';
    }
    .welcome-box {
        background: #fff6fb;
        border-radius: 18px;
        padding: 1.5em 2em;
        margin: 0 auto 2em auto;
        max-width: 600px;
        box-shadow: 0 2px 16px #ffd4f1;
        text-align: center;
    }

    .stButton>button {
        background-color: #ff96ec;
        color: #fff;
        border-radius: 8px;
        font-family: 'Quicksand', 'Montserrat', 'sans-serif';
        font-weight: bold;
        letter-spacing: 1px;
        border: 2px solid #ffd4f1;
        box-shadow: 0 0 12px 2px #ff96ec, 0 0 24px 4px #ffd4f1;
        transition: box-shadow 0.3s, background 0.3s, color 0.3s;
    }
    .stButton>button:hover {
        background-color: #ffd4f1;
        color: #ff96ec;
        box-shadow: 0 0 24px 6px #ff96ec, 0 0 48px 12px #ffd4f1;
        border: 2px solid #ff96ec;
    }
    .stButton>button:active {
        background-color: #ff96ec;
        color: #fff;
        box-shadow: 0 0 8px 2px #ff96ec, 0 0 16px 4px #ffd4f1;
    }
    .stButton>button:disabled {
        background-color: #ffd4f1;
        color: #aaa;
        box-shadow: none;
    }
    /* Hide Streamlit's default block background for even more transparency */
    [data-testid="stVerticalBlock"] {
        background: transparent !important;
    }
    
    
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background-image: url('https://i.imgur.com/CavrFKB.png');
    background-size: cover;
    background-repeat: no-repeat;
    background-position: center;
    font-size: 3.2rem;
    box-shadow: 2px 0 24px #ffd4f1;
    position: relative;
    overflow: hidden;
}
section[data-testid="stSidebar"]::before {
    content: "";
    position: absolute;
    inset: 0;
    background: rgba(255,246,251,0.85); /* less opaque overlay */
    z-index: 0;
}
section[data-testid="stSidebar"] > * {
    position: relative;
    z-index: 1;
}
</style>
""", unsafe_allow_html=True)


# Initialize session state variables
for key, default in [
    ("added_to_journal", False),
    ("selected_dish", None),
    ("selected_dishes", {}),
    ("menu_displayed", False)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- Render sidebar (handles login and navigation) ---

render_sidebar()

# --- Main content overlay for readability ---
st.markdown('<div class="main-content-overlay">', unsafe_allow_html=True)
if "user_id" not in st.session_state:
    # Show welcome box for not-logged-in users
    st.markdown(
        """
        <div class='welcome-box'>
            <img src= "https://imgur.com/TMVgTr0.png" class='bitzy-logo' alt='Bitzy Logo'>
            <span style='font-size:3rem;'>👋</span><br>
            <b>Welcome to Byte By Bite!</b><br>
            Log in with your Wellesley account to explore menus, track your meals, and let <span style="color:#ff96ec;">Bitzy</span> help you make the best dining choices.<br>
            <span style='font-size:2rem;'>🍽️💖</span>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    conn_user = create_user_connection(USER_DB)
    render_location(conn_user)
    selected_tab = st.session_state.get("selected_tab", "Home")
    if selected_tab == "Home":
        # Show Home card only
        st.markdown(
            """
            <div style="text-align: center;">
                <img src="https://imgur.com/TMVgTr0.png" width="200" style="
                filter: drop-shadow(0 0 24px #ff96ec) drop-shadow(0 0 48px #ffd4f1);
                margin-bottom: 1em;
                ">
            </div>
            <div style="
                background: rgba(255, 255, 255, 0.8);
                border-radius: 24px;
                padding: 2em;
                box-shadow: 0 0 24px 6px rgba(255, 150, 236, 0.5), 0 0 48px 12px rgba(255, 212, 241, 0.8);
                text-align: center;
                margin-bottom: 1.5em;
            ">
                <div class='main-title' style="
                    font-size: 5.0rem;
                    color: #ff96ec;
                    text-shadow: 3px 3px 0 #ffd4f1, 5px 5px 0 rgba(255, 150, 236, 0.5);
                ">Byte By Bite</div>
                <div class='subtitle' style="
                    font-size: 1.5rem;
                    color: #272936;
                "><b>Your personalized Wellesley dining experience, powered by <span style='color:#ff96ec;'>Bitzy</span>!</b></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown('</div>', unsafe_allow_html=True)

# --- Dynamic backgrounds for each tab ---
selected_tab = st.session_state.get("selected_tab", "Home")
tab_bg = {
    "Home": "https://i.postimg.cc/15V1mPTX/home.png",  # Updated with the new image URL
    "Food Journal": "https://i.imgur.com/Sff5Viy.png",  
    "Menu": "https://i.postimg.cc/gkW1WRvS/menu-1-Picsart-Ai-Image-Enhancer.png",  # Updated with the new image URL
    "Profile": "https://i.imgur.com/K1rxkdy.png"
}
bg_url = tab_bg.get(selected_tab, "")

if bg_url:
    st.markdown(
        f"""
        <style>
        html, body, .stApp {{
            background-image: url('{bg_url}');
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
            min-height: 100vh;
            height: 100vh;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        html, body, .stApp {
            background-image: none;
            background-color: #ffd4f1;
            min-height: 100vh;
            height: 100vh;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
