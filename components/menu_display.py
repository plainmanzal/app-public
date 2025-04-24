import streamlit as st
from datetime import datetime, date
import sqlite3
import pandas as pd
import os
import sys
from database.user_db import (
    log_daily_journal_entry,
    add_journal_dish,
    add_rating,
    ensure_dish_in_user_db,
)

LOCATION_MAP = {
    "Bao Pao": "Bae",
    "Bates": "Bates",
    "Stone Davis": "Stone",
    "Tower": "Tower"
}

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Now import from database package
from database import create_connection, log_daily_journal_entry, add_journal_dish, add_rating
from database.menu_db import WFR_DB

data = [
    {'location': 'Bae', 'meal': 'Breakfast', 'locationID': 96, 'mealID': 148},
    {'location': 'Bae', 'meal': 'Lunch', 'locationID': 96, 'mealID': 149},
    {'location': 'Bae', 'meal': 'Dinner', 'locationID': 96, 'mealID': 312},
    {'location': 'Bates', 'meal': 'Breakfast', 'locationID': 95, 'mealID': 145},
    {'location': 'Bates', 'meal': 'Lunch', 'locationID': 95, 'mealID': 146},
    {'location': 'Bates', 'meal': 'Dinner', 'locationID': 95, 'mealID': 311},
    {'location': 'Stone', 'meal': 'Breakfast', 'locationID': 131, 'mealID': 261},
    {'location': 'Stone', 'meal': 'Lunch', 'locationID': 131, 'mealID': 262},
    {'location': 'Stone', 'meal': 'Dinner', 'locationID': 131, 'mealID': 263},
    {'location': 'Tower', 'meal': 'Breakfast', 'locationID': 97, 'mealID': 153},
    {'location': 'Tower', 'meal': 'Lunch', 'locationID': 97, 'mealID': 154},
    {'location': 'Tower', 'meal': 'Dinner', 'locationID': 97, 'mealID': 310},
]

# Create a dataframe for ID lookups
dfKeys = pd.DataFrame(data)

# Get unique locations and meals
locations = sorted({item["location"] for item in data})
meals = sorted({item["meal"] for item in data})

def get_params(df, loc, meal):
    """Get location and meal IDs from the mapping."""
    matching_df = df[(df["location"] == loc) & (df["meal"] == meal)]
    if not matching_df.empty:
        location_id = matching_df["locationID"].iloc[0]
        meal_id = matching_df["mealID"].iloc[0]
        return location_id, meal_id
    else:
        return None, None
    
def get_all_allergens_and_prefs(conn_wfr):
    cursor = conn_wfr.cursor()
    cursor.execute("SELECT allergens, preferences FROM Dish")
    allergens = set()
    preferences = set()
    for row in cursor.fetchall():
        if row[0]:
            allergens.update([a.strip() for a in row[0].split(",") if a.strip()])
        if row[1]:
            preferences.update([p.strip() for p in row[1].split(",") if p.strip()])
    return sorted(allergens), sorted(preferences)


def display_menu_and_handle_journal(conn_user):
    if "user_id" not in st.session_state:
        st.warning("Please log in to continue.")
        st.stop()

    conn_wfr = create_connection(WFR_DB)
    cursor_wfr = conn_wfr.cursor()

    # --- Allergen/Preference Filtering ---
    all_allergens, all_prefs = get_all_allergens_and_prefs(conn_wfr)
    st.markdown(
        """
        <div style="background: #fff6fb; border-radius: 18px; padding: 1.2em 1.5em 1em 1.5em; margin: 0 auto 2em auto; max-width: 800px; box-shadow: 0 2px 16px #ffd4f1; text-align: center;">
            <span style="color: #ff96ec; font-size: 1.3rem; font-family: 'Quicksand', 'Montserrat', sans-serif; font-weight: bold; margin-bottom: 0.5em;">🍽️ Filter by Allergens & Preferences</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    selected_allergens = st.multiselect("Allergens to avoid", all_allergens, key="allergen_filter")
    selected_prefs = st.multiselect("Preferences", all_prefs, key="pref_filter")

    col1, col2, col3 = st.columns(3)
    with col1:
        location = st.selectbox("Location", ('Select Location', 'Bao Pao', 'Bates', 'Stone Davis', 'Tower'))
    with col2:
        meal = st.selectbox("Meal", ('Select Meal', 'Breakfast', 'Lunch', 'Dinner'))
    with col3:
        date_input = st.date_input("Enter the Date", date.today())
        date_str = date_input.strftime('%Y-%m-%d')

    # Get Menu
    if st.button("Get menu!"):
        st.session_state["meal"] = meal
        st.session_state["location"] = location
        st.session_state["date"] = date_str
        if location != 'Select Location' and meal != 'Select Meal':
            db_location = LOCATION_MAP.get(location, location)
            cursor_wfr.execute(
                """
                SELECT d.dish_name, d.dish_id, d.calories, d.protein, d.carbs, d.fat, d.allergens, d.preferences
                FROM Menu m
                JOIN Dish d ON m.dish_id = d.dish_id
                WHERE m.date=? AND m.dining_hall=? AND m.meal_type=?
                """,
                (date_str, db_location, meal)
            )
            menu_results = cursor_wfr.fetchall()

            # --- Filter menu_results based on selected allergens/preferences ---
            filtered_results = []
            for dish in menu_results:
                dish_allergens = [a.strip() for a in (dish[6] or "").split(",") if a.strip()]
                dish_prefs = [p.strip() for p in (dish[7] or "").split(",") if p.strip()]
                # Exclude dish if any selected allergen is present
                if any(a in dish_allergens for a in selected_allergens):
                    continue
                # If preferences are selected, only include dishes that match at least one
                if selected_prefs and not any(p in dish_prefs for p in selected_prefs):
                    continue
                filtered_results.append(dish)
            st.session_state["menu_results"] = filtered_results
        else:
            st.session_state["menu_results"] = []
    elif "menu_results" not in st.session_state:
        st.session_state["menu_results"] = []

    # Display the menu if results are available
    if st.session_state.get("menu_results"):
        for dish in st.session_state["menu_results"]:
            dish_name, dish_id, calories, protein, carbs, fat, allergens, preferences = dish
            col1, col2, col3 = st.columns([3, 1, 2])
            with col1:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #e6f7ff;
                        border-radius: 10px;
                        padding: 10px;
                        text-align: center;
                        box-shadow: 0 0 10px #99ccff;
                        ">
                        <b>{dish_name}</b>
                        <div style="font-size:0.85em;color:#ff96ec;">{allergens if allergens else ""}</div>
                        <div style="font-size:0.85em;color:#6ecb63;">{preferences if preferences else ""}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #ffe6f7;
                        border-radius: 10px;
                        padding: 10px;
                        text-align: center;
                        box-shadow: 0 0 10px #ff99cc;
                        ">
                        <b>{calories} cal</b>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col3:
                already_added = f"add_{dish_id}" in st.session_state["selected_dishes"]
                if already_added:
                    st.button("Added! ✅", key=f"added_{dish_id}", disabled=True)
                else:
                    if st.button("Add to Journal", key=f"add_{dish_id}"):
                        st.session_state["selected_dishes"][f"add_{dish_id}"] = dish
                        st.session_state["added_to_journal"] = True
                        st.rerun()

    # Handle journal entry if a dish has been added
    if st.session_state["added_to_journal"] and st.session_state["selected_dishes"]:
        st.divider()
        st.subheader("Finish Your Journal Entry!")
        date_input = st.date_input("Date", date.today())
        mood_input = st.selectbox("Mood", ["Happy", "Neutral", "Sad", "Excited", "Tired", "Angry", "Stressed"])
        notes_input = st.text_area("Notes")

        # Display all selected dishes
        for key, selected_dish in st.session_state["selected_dishes"].items():
            dish_name, dish_id, calories, protein, carbs, fat, allergens, preferences = selected_dish
            st.success(f"{dish_name} was added to your journal!")
            rating_input = st.slider(f"How would you rate {dish_name}?", 1, 5, key=f"rate_{key}")

            # Save the journal entry
        if st.button("✅ Save Journal Entry", key=f"save_journal_{dish_id}"):
            try:
                # 1. Ensure dish exists in user_data.db
                ensure_dish_in_user_db(
                    conn_user,
                    dish_id,
                    dish_name,
                    location,  # or db_location if you use a mapping
                    calories,
                    protein,
                    carbs,
                    fat
                )

                # 2. Save the journal entry and get its ID
                journal_id = log_daily_journal_entry(
                    conn_user,
                    st.session_state["user_id"],
                    date_input,
                    mood_input,
                    st.session_state.get("meal"),
                    notes_input,
                )

                # 3. Link the dish to the journal entry
                journal_dish_id = add_journal_dish(conn_user, journal_id, dish_id)

                # 4. Save the rating
                add_rating(conn_user, journal_dish_id, dish_id, rating_input)

                st.session_state["selected_dishes"] = {}
                st.session_state["added_to_journal"] = False
                st.success("Bitzy saved this journal entry and rating! 🎉")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save journal entry or rating: {e}")

    cursor_wfr.close()
    conn_wfr.close()