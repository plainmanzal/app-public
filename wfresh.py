import streamlit as st
import pandas as pd
import json
import requests
import datetime as dt

# From Assignment 5
def get_meals(date, locationId, mealId):
    url = f"https://dish.avifoodsystems.com/api/menu-items/week?date={date}&locationId={locationId}&mealId={mealId}"
    response = requests.get(url).json()
    return response


st.set_page_config(layout="wide")
st.title("Wellesley Fresh Menu")
# python -m streamlit run wfresh.py

with st.expander("Wellesley Fresh Menu"):
    st.write("Pick a dining hall and meal and enter the date to get the day's menu!")

#st.date_input("Enter a date", min_value=dt.date(2025,1,17))


col1, col2, col3 = st.columns(3)

with col1:
    location = st.selectbox("Location", ('Select Location','Bao Pao','Bates','Stone Davis','Tower'))
with col2:
    meal = st.selectbox("Meal", ('Select Meal','Breakfast', 'Lunch', 'Dinner'))
with col3:
    date = st.date_input("Enter the Date MM-DD-YYYY", min_value = dt.date(2025,1,17))
    # Need to figure out how to make sure they only submit the date in this format

# Conditionals
if location == "Bao Pao":
    if meal == "Breakfast":
        file = get_meals(date, 96, 148 )
    elif meal == "Lunch":
        file = get_meals(date, 96, 149)
    elif meal == "Dinner":
        file = get_meals(date, 96, 312)
    
elif location == "Bates":
    if meal == "Breakfast":
        file = get_meals(date, 95, 145)
    elif meal == "Lunch":
        file = get_meals(date, 95, 146)
    elif meal == "Dinner":
        file = get_meals(date, 95, 311)
    
elif location == "Tower":
    if meal == "Breakfast":
        file = get_meals(date, 97, 153)
    elif meal == "Lunch":
        file = get_meals(date, 97, 154)
    elif meal == "Dinner":
        file = get_meals(date, 97, 310)
    
elif location == "Stone Davis":
    if meal == "Breakfast":
        file = get_meals(date, 131, 261)
    elif meal == "Lunch":
        file = get_meals(date, 131, 262)
    elif meal == "Dinner":
        file = get_meals(date, 131, 263)

#file = "hi"
  
st.write("hello")
try:

        df = pd.DataFrame(file)
        
        if not df.empty:
            # drop all columns except 'name' and 'stationName'
            #df = df.drop(columns=[col for col in df.columns if col not in ['name', 'stationName', 'date']])
            
            df = df.filter(items=['date','name','stationName'])
            df = df.drop_duplicates()

            st.write("success")
            # group by stationName and ensure food items are unique
            grouped_df = df.groupby(['date','name'])['stationName'].apply(lambda x: list(set(x))).reset_index()

            #grouped_df = grouped_df.groupby('date')

            st.write("Menu for the week!")
            st.write(grouped_df)

            days_list = []

            for x in grouped_df['date'].unique():
                st.write("loop")
                df_new = grouped_df[grouped_df['date'] == date]
                days_list.append(df_new)
                #df_day = grouped_df('date')
            st.write(len(days_list))
            st.write(days_list)

            #df[df['date']==date]

            #get unique dates
            # iterate thru
            # create new dataframes


        
except Exception as e:
    st.write("Please enter valid choices for location, meal, and date!~~")
    print(f"error")

    
