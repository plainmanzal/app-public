import sqlite3
import streamlit as st
from datetime import date, time 
import pandas as pd

USER_DB = "user_data.db"
def create_connection(db_name):
    """Creates a database connection."""
    conn = sqlite3.connect(db_name)
    return conn

# first creating User Profile Database w/ functions-----------------------------------------

def create_user_tables():
    """Creates the necessary tables in the user database if they don't exist."""
    conn_user = create_connection(USER_DB)
    cursor = conn_user.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS User (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                goal TEXT,
                preferred_dining_hall TEXT,
                food_preferences TEXT
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Dish (
                dish_id INTEGER PRIMARY KEY AUTOINCREMENT,
                dish_name TEXT,
                dining_hall TEXT,
                calories INTEGER,
                protein INTEGER,
                carbs INTEGER,
                fat INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Rating (
                rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_dish_id INTEGER,
                dish_id INTEGER,
                rating INTEGER,
                FOREIGN KEY (journal_dish_id) REFERENCES Journal_Dish(journal_dish_id),
                FOREIGN KEY (dish_id) REFERENCES Dish(dish_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Daily_Journal (
                journal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                mood TEXT,
                meal_type TEXT,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES User(user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Journal_Dish (
                journal_dish_id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_id INTEGER,
                dish_id INTEGER,
                FOREIGN KEY (journal_id) REFERENCES Daily_Journal(journal_id),
                FOREIGN KEY (dish_id) REFERENCES Dish(dish_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Favorite_Dishes (
                favorite_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dish_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES User(user_id),
                FOREIGN KEY (dish_id) REFERENCES Dish(dish_id)
            )
        """)

        conn_user.commit()
    except sqlite3.Error as e:
        st.error(f"Error creating tables: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn_user:
            conn_user.close()

# adds a new user in the User table
def add_user(conn_user, username, email, goal=None, preferred_dining_hall=None, food_preferences=None):
    sql = ''' INSERT INTO User(username,email,goal,preferred_dining_hall,food_preferences)
              VALUES(?,?,?,?,?) '''
    cursor = conn_user.cursor()
    try:
        cursor.execute(sql, (username, email, goal, preferred_dining_hall, food_preferences))
        conn_user.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        st.error(f"Error adding user: {e}")
        return None

# gets a user from the User Table by their email
def get_user_by_email(conn_user, email):
    sql = ''' SELECT * FROM User WHERE email=? '''
    cursor = conn_user.cursor()
    cursor.execute(sql, (email,))
    return cursor.fetchone()

# logs a daily journal entry for the user
def log_daily_journal_entry(conn_user, user_id, date, mood, meal_type, notes):
    sql = ''' INSERT INTO Daily_Journal(user_id, date, mood, meal_type, notes)
              VALUES(?,?,?,?,?) '''
    cursor = conn_user.cursor()
    try:
        cursor.execute(sql, (user_id, date, mood, meal_type, notes))
        conn_user.commit()
        
        return cursor.lastrowid  # returns the journal id
    except sqlite3.Error as e:
        st.error(f"Error logging journal entry: {e}")
        return None

# adds a link between journal entry and a dish in the Journal_Dish table
def add_journal_dish(conn_user, journal_id, dish_id):
    sql = ''' INSERT INTO Journal_Dish(journal_id, dish_id) VALUES (?,?) '''
    cursor = conn_user.cursor()
    try:
        cursor.execute(sql, (journal_id, dish_id))
        conn_user.commit()
        
        return cursor.lastrowid
    except sqlite3.Error as e:
        st.error(f"Error adding journal dish entry: {e}")
        return None


# adds a rating for a dish in a journal entry
def add_rating(conn_user, journal_dish_id, dish_id, rating):
    sql = ''' INSERT INTO Rating(journal_dish_id, dish_id, rating) VALUES (?,?,?) '''
    cursor = conn_user.cursor()
    try:
        cursor.execute(sql, (journal_dish_id, dish_id, rating))
        conn_user.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        st.error(f"Error adding rating: {e}")
        return None


# gets all dishes associated with a journal entry

def get_journal_dishes(conn_user, journal_id):
    # Get dish_ids from Journal_Dish in user_data.db
    sql = "SELECT dish_id FROM Journal_Dish WHERE journal_id = ?"
    cursor = conn_user.cursor()
    cursor.execute(sql, (journal_id,))
    dish_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()

    # Now get dish info from wellesley_fresh_data.db
    from database.menu_db import create_connection as create_menu_connection, WFR_DB
    conn_menu = create_menu_connection(WFR_DB)
    cursor_menu = conn_menu.cursor()
    dishes = []
    for dish_id in dish_ids:
        cursor_menu.execute(
            "SELECT dish_id, dish_name, calories, protein, carbs, fat FROM Dish WHERE dish_id = ?",
            (dish_id,)
        )
        result = cursor_menu.fetchone()
        if result:
            dishes.append(result)
    cursor_menu.close()
    conn_menu.close()
    return dishes

# gets a user's journal entries for a given date
def get_user_journal_entries(conn_user, user_id, date):
    sql = """
        SELECT dj.journal_id, dj.date, dj.mood, dj.meal_type, dj.notes
        FROM Daily_Journal dj
        WHERE dj.user_id = ? AND dj.date = ?
    """
    # cursor = conn_user.cursor()
    # cursor.execute(sql, (user_id, date))
    
    # return cursor.fetchall()
    cursor = conn_user.cursor()
    try:
        cursor.execute(sql, (user_id, date))
        return cursor.fetchall()
    finally:
        cursor.close()

# gets all ratings for a given dish
def get_ratings_for_dish(conn_user, dish_id):
    sql = """
        SELECT r.rating
        FROM Rating r
        WHERE r.dish_id = ?
    """
    cur = conn_user.cursor()
    cur.execute(sql, (dish_id,))
    return cur.fetchall()

# adding favorite dish to database
def add_favorite_dish(conn_user, user_id, dish_id):
    sql = ''' INSERT INTO Favorite_Dishes (user_id, dish_id) VALUES (?, ?) '''
    cursor = conn_user.cursor()
    try:
        cursor.execute(sql, (user_id, dish_id))
        conn_user.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        st.error(f"Error adding favorite dish: {e}")
        return None

# getting favorite dishes
def get_favorite_dishes(conn_user, user_id):
    sql = """
    SELECT d.dish_name, d.calories, d.protein, d.carbs, d.fat
    FROM Favorite_Dishes fd
    JOIN Dish d ON fd.dish_id = d.dish_id
    WHERE fd.user_id = ?
    """
    cursor = conn_user.cursor()
    try:
        cursor.execute(sql, (user_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Error fetching favorite dishes: {e}")
        return []

# removing favorite dishes from database
def remove_favorite_dish(conn_user, user_id, dish_id):
    sql = ''' DELETE FROM Favorite_Dishes WHERE user_id = ? AND dish_id = ? '''
    cursor = conn_user.cursor()
    try:
        cursor.execute(sql, (user_id, dish_id))
        conn_user.commit()
    except sqlite3.Error as e:
        st.error(f"Error removing favorite dish: {e}")

# showing the user's favorite dishes
def display_user_dish_ratings(conn_user, user_id):
    # Add CSS for styling
    st.markdown("""
    <style>
    .bitzy-dish-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        box-shadow: 0 0 8px #e4ffa6;
        margin-bottom: 10px;
        padding: 10px 0;
        font-family: 'Quicksand', 'Montserrat', sans-serif;
    }
    .bitzy-dish-cell {
        flex: 1;
        text-align: center;
        font-size: 1.08rem;
        color: #272936;
        font-weight: 500;
    }
    .bitzy-dish-cell.name {
        flex: 2;
        font-weight: bold;
        color: #272936;
        font-size: 1.13rem;
    }
    .bitzy-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #ffffff;
        background-color: #ff96ec;
        padding: 0.5em 1em;
        border-radius: 8px;
        margin: 1em 0;
        text-align: center;
        font-family: 'Quicksand', 'Montserrat', sans-serif;
        box-shadow: 0 0 8px #ff96ec;
    }
    </style>
    """, unsafe_allow_html=True)

    sql = """
    SELECT r.rating, d.dish_name
    FROM Rating r
    JOIN Journal_Dish jd ON r.journal_dish_id = jd.journal_dish_id
    JOIN Daily_Journal dj ON jd.journal_id = dj.journal_id
    JOIN Dish d ON r.dish_id = d.dish_id
    WHERE dj.user_id = ?
    """
    cursor = conn_user.cursor()
    try:
        cursor.execute(sql, (user_id,))
        df = pd.DataFrame(cursor.fetchall(), columns=["Rating", "Dish Name"])
        df = df.sort_values(by="Rating", ascending=False)

        # Display header
        st.markdown("<div class='bitzy-header'>Here are your top 5 dishes!</div>", unsafe_allow_html=True)

        # Display rows
        for _, row in df.head(5).iterrows():
            st.markdown(
                f"""
                <div class='bitzy-dish-row'>
                    <div class='bitzy-dish-cell name'>{row['Dish Name']}</div>
                    <div class='bitzy-dish-cell'>{row['Rating']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    except sqlite3.Error as e:
        st.error(f"Error fetching user dish ratings: {e}")
    finally:
        cursor.close()

def ensure_dish_in_user_db(conn_user, dish_id, dish_name, dining_hall, calories, protein, carbs, fat):
    # Check if dish exists in user_data.db
    cursor = conn_user.cursor()
    cursor.execute("SELECT dish_id FROM Dish WHERE dish_id = ?", (dish_id,))
    exists = cursor.fetchone()
    if not exists:
        cursor.execute(
            "INSERT INTO Dish (dish_id, dish_name, dining_hall, calories, protein, carbs, fat) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (dish_id, dish_name, dining_hall, calories, protein, carbs, fat)
        )
        conn_user.commit()
    cursor.close()
    

# def get_user_nutrition_data(conn_user, user_id):
#     sql = """
#         SELECT
#             dj.date,
#             d.dish_name,
#             d.calories,
#             d.protein,
#             d.carbs,
#             d.fat
#         FROM Daily_Journal dj
#         JOIN Journal_Dish jd ON dj.journal_id = jd.journal_id
#         JOIN Dish d ON jd.dish_id = d.dish_id
#         WHERE dj.user_id = ?
#         ORDER BY dj.date DESC
#     """
#     df = pd.read_sql_query(sql, conn_user, params=(user_id,))
#     return df


# gets all dishes in the Dish table
def display_journal(conn_user, user_id):
    st.session_state["user_id"] = user_id

    # --- Bitzy/Gen-Z CSS ---
    st.markdown("""
    <style>
    .bitzy-dish-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: rgba(255, 255, 255, 0.9);

        border-radius: 10px;
        box-shadow: 0 0 8px #e4ffa6;
        margin-bottom: 10px;
        padding: 10px 0;
        font-family: 'Quicksand', 'Montserrat', sans-serif;
    }
    .bitzy-dish-cell {
        flex: 1;
        text-align: center;
        font-size: 1.08rem;
        color: #272936;
        font-weight: 500;
        
    }
    .bitzy-dish-cell.name {
        flex: 2;
        font-weight: bold;
        color: #272936;
        font-size: 1.13rem;
    }
    .bitzy-mood-notes {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        padding: 0.7em 1em;
        margin: 0.5em 0 1em 0;
        font-size: 1.1rem;
        color: #272936;
        font-family: 'Quicksand', 'Montserrat', sans-serif;
        box-shadow: 0 0 8px #ffd4f1;
    }
    .bitzy-meal-type {
        font-size: 1.3rem;
        font-weight: bold;
        color: #ffffff;
        background-color: #ff96ec;
        padding: 0.5em 1em;
        border-radius: 8px;
        margin: 1em 0;
        text-align: center;
        font-family: 'Quicksand', 'Montserrat', sans-serif;
        box-shadow: 0 0 8px #ff96ec;
    }
    </style>
    """, unsafe_allow_html=True)

    if "user_id" not in st.session_state:
        st.error("You must be logged in to view your journal.")
        return

    conn = create_connection("user_data.db")
    selected_date = st.date_input("Select a date")
    journals = get_user_journal_entries(conn, user_id, selected_date.isoformat())

    if journals:
        # Group journals by meal type
        grouped_journals = {}
        for journal in journals:
            meal_type = journal[3]
            if meal_type not in grouped_journals:
                grouped_journals[meal_type] = []
            grouped_journals[meal_type].append(journal)

        for meal_type, entries in grouped_journals.items():
            # Display meal type header
            st.markdown(f"<div class='bitzy-meal-type'>{meal_type}</div>", unsafe_allow_html=True)

            for journal in entries:
                journal_id = journal[0]
                dishes = get_journal_dishes(conn, journal_id)

                if dishes:
                    # Header
                    st.markdown(
                        """
                        <div class='bitzy-dish-row' style="font-weight:bold; background:#e4ffa6;">
                            <div class='bitzy-dish-cell name'>Dish Name</div>
                            <div class='bitzy-dish-cell'>Calories</div>
                            <div class='bitzy-dish-cell'>Protein (g)</div>
                            <div class='bitzy-dish-cell'>Carbs (g)</div>
                            <div class='bitzy-dish-cell'>Fat (g)</div>
                            <div class='bitzy-dish-cell'>Avg. Rating</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Rows
                    for dish in dishes:
                        dish_id, name, cal, protein, carbs, fat = dish
                        ratings = get_ratings_for_dish(conn, dish_id)
                        avg_rating = round(sum(r[0] for r in ratings) / len(ratings), 1) if ratings else "N/A"

                        st.markdown(
                            f"""
                            <div class='bitzy-dish-row'>
                                <div class='bitzy-dish-cell name'>{name}</div>
                                <div class='bitzy-dish-cell'>{cal}</div>
                                <div class='bitzy-dish-cell'>{protein}</div>
                                <div class='bitzy-dish-cell'>{carbs}</div>
                                <div class='bitzy-dish-cell'>{fat}</div>
                                <div class='bitzy-dish-cell'>{avg_rating}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    # Mood and Notes
                    st.markdown(f"<div class= 'bitzy-mood-notes'; style='margin:0.5em 0 1em 0;'><b>Mood:</b> {journal[2]}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class= 'bitzy-mood-notes'; style='margin-bottom:1.5em;'><b>Notes:</b> {journal[4]}</div>", unsafe_allow_html=True)
            
    else:
        st.info("No journal entries for that date.")
        
#def display_favorites(conn_user, user_id):
    