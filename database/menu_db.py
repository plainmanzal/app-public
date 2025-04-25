import sqlite3
import streamlit as st
import requests
import datetime

WFR_DB = "wellesley_fresh_data.db"

def create_connection(db_name):
    """Creates a database connection."""
    conn = sqlite3.connect(db_name)
    return conn

def create_wfr_tables():
    """Creates tables for the Wellesley Fresh database."""
    conn_wfr = create_connection(WFR_DB)
    cursor = conn_wfr.cursor()
    try:
        cursor.execute("""
              CREATE TABLE IF NOT EXISTS Dish (
                dish_id INTEGER PRIMARY KEY AUTOINCREMENT,
                dish_name TEXT,
                dining_hall TEXT,
                calories INTEGER,
                protein INTEGER,
                carbs INTEGER,
                fat INTEGER,
                allergens TEXT,
                preferences TEXT
                )
            """)
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS Menu (
                    menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dish_id INTEGER,
                    date TEXT,
                    meal_type TEXT,
                    dining_hall TEXT,
                    FOREIGN KEY (dish_id) REFERENCES Dish(dish_id)
                )
            """)
        cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_menu_date_dining_meal
                ON Menu (date, dining_hall, meal_type)
            """)
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS W_Rating (
                    dish_id INTEGER PRIMARY KEY,
                    avg_rating REAL,
                    total_ratings INTEGER,
                    most_recent_served TEXT,
                    most_common_dining_hall TEXT,
                    FOREIGN KEY (dish_id) REFERENCES Dish(dish_id)
                )
            """)
        conn_wfr.commit()
    except sqlite3.Error as e:
        st.error(f"Error creating tables: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn_wfr:
            conn_wfr.close()


# updates the W_Rating table with the average rating for a dish
def update_w_rating(conn_wfr, dish_id):
    conn_user = create_connection(USER_DB)
    cursor_user = conn_user.cursor()
    try:
        try:
            ratings = get_ratings_for_dish(conn_user, dish_id)
        finally:
            if conn_user:
                conn_user.close()
        if ratings:
            total_rating = sum(rating[0] for rating in ratings)
            num_ratings = len(ratings)
            average_rating = total_rating / num_ratings
        else:
            average_rating = 0  # default to 0 if no ratings

        cursor_wfr = conn_wfr.cursor()
        # checks if the dish already has a W_Rating
        cursor_wfr.execute("SELECT * FROM W_Rating WHERE dish_id=?", (dish_id,))
        existing_rating = cursor_wfr.fetchone()
        if existing_rating:
            # updates the existing rating
            cursor_wfr.execute("""
                UPDATE W_Rating
                SET avg_rating=?, total_ratings=?
                WHERE dish_id=?
            """, (average_rating, num_ratings, dish_id))
        else:
            # inserts a new rating
            cursor_wfr.execute("""
                INSERT INTO W_Rating (dish_id, avg_rating, total_ratings, most_recent_served, most_common_dining_hall)
                VALUES (?,?,?,?,?)
            """, (dish_id, average_rating, num_ratings, get_most_recent_served(conn_wfr,dish_id),get_most_common_dining_hall(conn_wfr,dish_id)))
        conn_wfr.commit()
    except sqlite3.Error as e:
        st.error(f"Error updating W_Rating: {e}")
    finally:
        if cursor_user:
            cursor_user.close()
        if conn_user:
            conn_user.close()
        if cursor_wfr:
            cursor_wfr.close()
        if conn_wfr:
            conn_wfr.close()

# gets the most recent date a dish was served
def get_most_recent_served(conn_wfr, dish_id):
    cursor = conn_wfr.cursor()
    cursor.execute(
        """
        SELECT MAX(date)
        FROM Menu
        WHERE dish_id = ?
        """,
        (dish_id,),
    )
    result = cursor.fetchone()
    return result[0] if result else None

# returns the dining hall where a dish is most commonly served
def get_most_common_dining_hall(conn_wfr, dish_id):
    cursor = conn_wfr.cursor()
    cursor.execute(
        """
        SELECT dining_hall
        FROM Menu
        WHERE dish_id = ?
        GROUP BY dining_hall
        ORDER BY COUNT(*) DESC
        LIMIT 1
        """,
        (dish_id,),
    )
    result = cursor.fetchone()
    return result[0] if result else None

def get_meals(date_str, location_id, meal_id, conn_wfr, location, meal_str):
    url = f"https://dish.avifoodsystems.com/api/menu-items/week?date={date_str}&locationId={location_id}&mealId={meal_id}"
    cursor = None  # Initialize cursor to None
    try:
        response = requests.get(url)
        menu_data_all_week = response.json()

        if isinstance(menu_data_all_week, list):
            cursor = conn_wfr.cursor()
            inserted_dish_count = 0
            inserted_menu_item_count = 0
            target_date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

            for item in menu_data_all_week:
                api_date_str = item.get('date')
                if api_date_str:
                    api_date_obj = datetime.datetime.strptime(api_date_str.split('T')[0], '%Y-%m-%d').date()
                    if api_date_obj == target_date_obj:
                        dish_name = item.get('name', 'Unknown Dish').strip()
                        if not dish_name:
                            continue

                        nutritionals = item.get('nutritionals') or {}

                        def safe_int(value):
                            try:
                                return int(float(value)) if value is not None else None
                            except (ValueError, TypeError):
                                return None
                        def extract_names(lst):
                            # Handles both list of strings and list of dicts with 'name'
                            if not lst:
                                return []
                            if isinstance(lst[0], dict):
                                return [d.get("name", "") for d in lst if "name" in d]
                            return [str(x) for x in lst]
                        
                        allergens = ",".join(extract_names(item.get('allergens', [])))
                        preferences = ",".join(extract_names(item.get('preferences', [])))
                        calories = safe_int(nutritionals.get('calories'))
                        protein = safe_int(nutritionals.get('protein'))
                        carbs = safe_int(nutritionals.get('carbohydrates'))
                        fat = safe_int(nutritionals.get('fat'))

                        # Check if the dish already exists
                        cursor.execute("SELECT dish_id FROM Dish WHERE dish_name = ? AND dining_hall = ?", (dish_name, location))
                        existing_dish = cursor.fetchone()
                        if "added_to_journal" not in st.session_state:
                            st.session_state["added_to_journal"] = False
                        if existing_dish:
                            dish_id = existing_dish[0]
                        else:
                            cursor.execute("""
                                INSERT INTO Dish (dish_name, dining_hall, calories, protein, carbs, fat, allergens, preferences)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (dish_name, location, calories, protein, carbs, fat, allergens, preferences))
                            dish_id = cursor.lastrowid
                            inserted_dish_count += 1

                        # Check if the menu item already exists
                        cursor.execute("""
                            SELECT menu_id FROM Menu
                            WHERE dish_id = ? AND date = ? AND meal_type = ? AND dining_hall = ?
                        """, (dish_id, date_str, meal_str, location))
                        existing_menu_item = cursor.fetchone()

                        if not existing_menu_item:
                            cursor.execute("""
                                INSERT INTO Menu (dish_id, date, meal_type, dining_hall)
                                VALUES (?, ?, ?, ?)
                            """, (dish_id, date_str, meal_str, location))
                            inserted_menu_item_count += 1

            conn_wfr.commit()

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        st.error(f"Bitzy had an unexpected error :( : {e}\n\nDetails:\n{error_details}")
    finally:
        if cursor:
            cursor.close()

# gets dishes from the menu for a specific date and dining hall------------------
def get_dishes_from_menu(conn_wfr, date, dining_hall):
    cursor = conn_wfr.cursor()
    cursor.execute("""
        SELECT d.dish_name, d.dish_id, d.calories, d.protein, d.carbs, d.fat
        FROM Menu m
        JOIN Dish d ON m.dish_id = d.dish_id
        WHERE m.date = ? AND m.dining_hall = ?
        """, (date, dining_hall))
    dishes = cursor.fetchall()
    return dishes

def update_all_menus_for_week(start_date_str, conn_wfr):
    """
    Fetches and updates menu data for all dining halls and meal types for the week
    starting from start_date_str (format: 'YYYY-MM-DD').
    """
    import datetime

    # Use your mapping for location and meal IDs
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

    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    for day_offset in range(7):  # For each day in the week
        date_obj = start_date + datetime.timedelta(days=day_offset)
        date_str = date_obj.strftime('%Y-%m-%d')
        for entry in data:
            get_meals(
                date_str=date_str,
                location_id=entry['locationID'],
                meal_id=entry['mealID'],
                conn_wfr=conn_wfr,
                location=entry['location'],
                meal_str=entry['meal']
            )