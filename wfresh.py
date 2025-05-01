import streamlit as st
from components.auth import render_sidebar
from datetime import timedelta, date
from components.menu_display import display_menu_and_handle_journal
from components.auth import render_location
from database.user_db import create_connection as create_user_connection, USER_DB
from database.menu_db import create_wfr_tables, update_all_menus_for_week, create_connection as create_menu_connection
from database.user_db import display_user_dish_ratings
from database.menu_db import create_connection, WFR_DB, update_all_menus_for_week
import os
import requests

def download_db_from_github():
    db_path = st.secrets["github"]["db_path"]
    token = st.secrets["github"]["token"]
    repo = st.secrets["github"]["repo"]
    # Construct the raw URL for the file in your repo
    url = f"https://raw.githubusercontent.com/{repo}/main/{db_path}"
    headers = {"Authorization": f"token {token}"}
    if not os.path.exists(db_path):
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            with open(db_path, "wb") as f:
                f.write(r.content)
        else:
            st.error("Failed to download user_data.db from GitHub.")

download_db_from_github()

st.set_page_config(
    page_title="Byte By Bite",  # This is the tab title
    page_icon="https://imgur.com/TMVgTr0.png",  # This is your Bitzy logo (favicon)
    layout="wide"  # Optional: makes your app use the full width
)

# --- Only update menus once per week for all users (using a file flag) ---
def menu_update_needed(monday_str):
    flag_file = f".menu_updated_{monday_str}"
    return not os.path.exists(flag_file)

def set_menu_updated(monday_str):
    flag_file = f".menu_updated_{monday_str}"
    with open(flag_file, "w") as f:
        f.write("updated")

today = date.today()
monday = today - timedelta(days=today.weekday())
monday_str = monday.strftime('%Y-%m-%d')

if menu_update_needed(monday_str):
    conn_wfr = create_connection(WFR_DB)
    with st.spinner(f"Updating menus for the week of {monday_str}..."):
        update_all_menus_for_week(monday_str, conn_wfr)
    conn_wfr.close()
    set_menu_updated(monday_str)
    st.success("Menus updated for this week!")

def get_journal_streak(conn_user, user_id):
    """Returns the current streak (in days) of consecutive journal entries."""
    cur = conn_user.cursor()
    cur.execute("""
        SELECT DISTINCT date
        FROM Daily_Journal
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))
    dates = [row[0] for row in cur.fetchall()]
    cur.close()
    if not dates:
        return 0

    # Convert to date objects and sort descending
    date_objs = sorted([date.fromisoformat(d) for d in dates], reverse=True)
    streak = 1
    for i in range(1, len(date_objs)):
        if (date_objs[i-1] - date_objs[i]).days == 1:
            streak += 1
        else:
            break
    return streak

# --- Google Fonts for extra polish ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@700;900&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Pacifico&display=swap" rel="stylesheet">
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
        def get_top_5_dishes(conn_user, user_id):
            # Get top 5 dishes by average rating, then by count
            sql = """
                SELECT d.dish_name, AVG(r.rating) as avg_rating, COUNT(r.rating) as num_ratings
                FROM Rating r
                JOIN Dish d ON r.dish_id = d.dish_id
                JOIN Journal_Dish jd ON r.journal_dish_id = jd.journal_dish_id
                JOIN Daily_Journal dj ON jd.journal_id = dj.journal_id
                WHERE dj.user_id = ?
                GROUP BY d.dish_id
                HAVING num_ratings > 0
                ORDER BY avg_rating DESC, num_ratings DESC
                LIMIT 5
            """
            cur = conn_user.cursor()
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()
            cur.close()
            return rows
        def get_bitzy_reminders(conn_user, user_id):
            # Get user's 4- or 5-star dishes
            cur = conn_user.cursor()
            cur.execute("""
            SELECT DISTINCT d.dish_id, d.dish_name
            FROM Rating r
            JOIN Dish d ON r.dish_id = d.dish_id
            JOIN Journal_Dish jd ON r.journal_dish_id = jd.journal_dish_id
            JOIN Daily_Journal dj ON jd.journal_id = dj.journal_id
            WHERE dj.user_id = ? AND r.rating >= 4
            """, (user_id,))
            fav_dishes = cur.fetchall()
            if not fav_dishes:
                cur.close()
                return []
            conn_menu = create_menu_connection(WFR_DB)
            cur_menu = conn_menu.cursor()
            today = date.today()
            cur_menu.execute("""
                SELECT m.date, m.dining_hall, m.meal_type, d.dish_name
                FROM Menu m
                JOIN Dish d ON m.dish_id = d.dish_id
                WHERE m.date = ?
                """, (today.strftime('%Y-%m-%d'),))
            menu_rows = cur_menu.fetchall()
            cur_menu.close()
            conn_menu.close()

            # Find matches
            reminders = []
            fav_dish_names = {name for _, name in fav_dishes}
            for menu_date, hall, meal, dish_name in menu_rows:
                if dish_name in fav_dish_names:
                    reminders.append({
                    "dish_name": dish_name,
                    "dining_hall": hall,
                    "meal": meal,
                    "date": menu_date
                    })
            return reminders

        
        st.markdown(
        """
        <div style="
            text-align: center;
            margin-top: 0.5em;
            margin-bottom: -1.5em;
            position: relative;
            z-index: 10;
        ">
            <span style="
                font-family: 'Pacifico', cursive;
                font-size: 2.4rem;
                color: #fff;
                text-shadow:
                    0 0 8px #ff96ec,
                    0 0 16px #ff96ec,
                    0 0 24px #ffd4f1,
                    0 0 32px #ff96ec;
                background: rgba(255, 150, 236, 0.15);
                border-radius: 18px;
                padding: 0.3em 1.2em;
                display: inline-block;
                letter-spacing: 2px;
            ">
                Smart Bytes, Tasty Bites
            </span>
        </div>
         """,
        unsafe_allow_html=True
    )
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
                Scroll to see your <span style='color:#ff96ec;'>reminders, streak, and Top 5 dishes</span>!</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        conn_user = create_user_connection(USER_DB)
        reminders = get_bitzy_reminders(conn_user, st.session_state.user_id)
        if reminders:
            st.markdown(
                """
                <div style="
                    background: #ffffff;
                    border-radius: 18px;
                    padding: 2em 1.5em 2em;
                    margin: 1.5em auto 2em auto;
                    max-width: 600px;
                    box-shadow: 0 2px 24px #ff96ec;
                    text-align: center;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 24px;
                ">
                    <span style="
                        color: #ff96ec;
                        font-size:3.5rem;
                        font-family: 'Quicksand', 'Montserrat', sans-serif;
                        font-weight: bold;
                        text-shadow: 
                            0 0 4px #ff96ec, 
                            0 0 8px #ff96ec,  
                            0 0 14px #ff96ec;
                    ">
                        <b>Bitzy Reminder!</b><br>
                    </span>
                    <img src="https://i.postimg.cc/44Ks8YcS/bitzy-happy.png" alt="Bitzy Happy" style="width: 120px; height: 120px;">
                    <span style="
                        color: #ff96ec;
                        font-size: 1.5rem;
                        font-family: 'Quicksand', 'Montserrat', sans-serif;
                        font-weight: bold;
                    ">
                    <br>
                        Your favorite dish is back this week:
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
            for r in reminders:
                when = "today" if r["date"] == date.today().strftime('%Y-%m-%d') else f'on {r["date"]}'
                st.markdown(
                    f"""
                    <div style="
                        background: #fff6fb;
                        border-radius: 12px;
                        padding: 1em;
                        margin: 0.8em auto;
                        max-width: 500px;
                        box-shadow: 0 0 24px 4px #ff96ec, 0 0 48px 8px #ffd4f1;
                        text-align: center;
                        font-family: 'Quicksand', 'Montserrat', sans-serif;
                        color: #272936;
                        position: relative;
                    ">
                        <span style="
                            color: #ff96ec;
                            font-size: 1.2rem;
                            font-weight: bold;
                            text-shadow: 0 0 8px #ff96ec, 0 0 16px #ffd4f1;
                        ">
                            <b>{r['dish_name']}</b>
                        </span><br>
                        <span style="font-size: 1rem; color: #272936;">
                            at <b>{r['dining_hall']}</b> for <b>{r['meal']}</b> {when}!
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            st.markdown("</span></div>", unsafe_allow_html=True)
        streak = get_journal_streak(conn_user, st.session_state.user_id)
        if streak >= 2:
                st.markdown(
                    f"""
                    <div style="
                        background: #fff6fb;
                        border-radius: 18px;
                        padding: 1.5em 1.5em 1.2em 1.5em;
                        margin: 2em auto 2em auto;
                        max-width: 600px;
                        box-shadow: 0 0 32px 8px #ff96ec, 0 0 64px 16px #ffd4f1;
                        text-align: center;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        gap: 18px;
                        position: relative;
                    ">
                        <img src="https://i.postimg.cc/RZ58LF1K/bitzy-excited.png" alt="Bitzy Excited" style="width: 90px; height: 90px;">
                        <span style="
                            color: #ff96ec;
                            font-size: 2rem;
                            font-family: 'Pacifico', cursive;
                            font-weight: bold;
                            text-shadow: 0 0 12px #ff96ec, 0 0 24px #ffd4f1;
                            margin-bottom: 0.5em;
                        ">
                            Bitzy's Weekly Streak!
                        </span>
                        <span style="
                            color: #272936;
                            font-size: 1.3rem;
                            font-family: 'Quicksand', 'Montserrat', sans-serif;
                            font-weight: bold;
                        ">
                            <b>{streak} days in a row!</b> <br>
                            Keep it up and earn more Bitzy badges!
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        elif streak == 1:
                st.markdown(
                    """
                    <div style="
                        background: #fff6fb;
                        border-radius: 18px;
                        padding: 1.2em 1.5em 1em 1.5em;
                        margin: 2em auto 2em auto;
                        max-width: 600px;
                        box-shadow: 0 0 16px 4px #ff96ec, 0 0 32px 8px #ffd4f1;
                        text-align: center;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        gap: 18px;
                        position: relative;
                    ">
                        <img src="https://i.postimg.cc/44Ks8YcS/bitzy-happy.png" alt="Bitzy Happy" style="width: 70px; height: 70px;">
                        <span style="
                            color: #ff96ec;
                            font-size: 1.3rem;
                            font-family: 'Pacifico', cursive;
                            font-weight: bold;
                            text-shadow: 0 0 8px #ff96ec, 0 0 16px #ffd4f1;
                            margin-bottom: 0.5em;
                        ">
                            Bitzy’s Streak Started!
                        </span>
                        <span style="
                            color: #272936;
                            font-size: 1.1rem;
                            font-family: 'Quicksand', 'Montserrat', sans-serif;
                            font-weight: bold;
                        ">
                            1 day in a row! Come back tomorrow for a streak!
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # --- Top 5 Dishes ---
        top5 = get_top_5_dishes(conn_user, st.session_state.user_id)
        if top5:
            st.markdown(
            """
            <div style="
                background: #ffffff;
                border-radius: 18px;
                padding:  2em 1.5em 2em;
                margin: 1.5em auto 2em auto;
                max-width: 600px;
                box-shadow: 0 2px 24px #ff96ec;
                text-align: center;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 24px;
            ">
                <img src="https://i.postimg.cc/h4xxktW2/bitzy-neutral.png" alt="Bitzy Neutral" style="width: 80px; height: 80px; border-radius: 50%;">
                <span style="color: #ff96ec; font-size: 1.5rem; font-family: 'Quicksand', 'Montserrat', sans-serif; font-weight: bold;">
                Here are your Top 5 Dishes!
                </span>
            </div>
            """,
            unsafe_allow_html=True
            )
            for rank, (dish_name, avg_rating, num_ratings) in enumerate(top5, start=1):
                st.markdown(
                    f"""
                    <div style="
                    background: #ffffff;
                    border-radius: 12px;
                    padding: 1em;
                    margin: 0.8em auto;
                    max-width: 500px;
                    box-shadow: 0 0 24px 4px #ff96ec, 0 0 48px 8px #ffd4f1;
                    text-align: center;
                    font-family: 'Quicksand', 'Montserrat', sans-serif;
                    color: #272936;
                    position: relative;
                    ">
                    <div style="
                        position: absolute;
                        top: -40px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: #ff96ec;
                        color: #ffffff;
                        font-size: 1.5rem;
                        font-weight: bold;
                        padding: 0.2em 0.8em;
                        border-radius: 12px;
                        margin-bottom: 20px
                        box-shadow: 0 0 12px #ff96ec;
                    ">
                    #{rank}
                    </div>
                    <b style="font-size: 1.5rem; color: #ff96ec;">{dish_name}</b><br>
                    <span style="font-size: 1.2rem;">{avg_rating:.2f} ⭐ ({num_ratings} rating{'s' if num_ratings != 1 else ''})</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        conn_user.close()
        

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
