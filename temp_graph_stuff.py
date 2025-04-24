import numpy
import plotly.express as px
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from database.user_db import create_connection as create_user_connection, USER_DB


# creating the data visualizations
def create_plots():
    macros_dropdown = st.selectbox('What do you want to track?', ('carbs', 'fat', 'calories', 'protein'))
    
    sql = """
        SELECT d.dish_name, dj.date, d.calories, d.protein, d.carbs, d.fat
        FROM Daily_Journal dj
        JOIN Journal_Dish jd ON dj.journal_id = jd.journal_id
        JOIN Dish d ON jd.dish_id = d.dish_id
        WHERE dj.user_id = ?
    """
    conn_user = create_user_connection(USER_DB)
    user_id = st.session_state.get("user_id")
    
    #cursor = conn_user.cursor()
    #cursor.execute(sql)
    #data = cursor.fetchall()

    df = get_user_nutrition_data(conn_user, user_id)
    #df = pd.DataFrame(data, columns=['dish_name', 'calories', 'protein', 'carbs', 'fat'])

    if not df.empty:
        # Creating bar chart tracking macro intake
        fig = px.bar(df, x='date', y=macros_dropdown, title = f"{macros_dropdown} Intake Over Time")
        st.write(fig)
    else:
        st.write("No data available for the selected macro.")


def get_user_nutrition_data(conn_user, user_id):
    sql = """
        SELECT
            dj.date,
            dj.meal_type,
            d.dish_name,
            d.calories,
            d.protein,
            d.carbs,
            d.fat
        FROM Daily_Journal dj
        JOIN Journal_Dish jd ON dj.journal_id = jd.journal_id
        JOIN Dish d ON jd.dish_id = d.dish_id
        WHERE dj.user_id = ?
        ORDER BY dj.date DESC
    """
    df = pd.read_sql_query(sql, conn_user, params=(user_id,))
    return df

def create_plots():
    st.markdown("""
    <style>
    .bitzy-plot-box {
        background: #fff6fb;
        border-radius: 18px;
        padding: 2em 2em 1.5em 2em;
        margin: 0 auto 2em auto;
        max-width: 800px;
        box-shadow: 0 2px 16px #ffd4f1;
        text-align: center;
    }
    .bitzy-plot-title {
        color: #ff96ec;
        font-size: 1.6rem;
        font-family: 'Quicksand', 'Montserrat', sans-serif;
        font-weight: bold;
        margin-bottom: 1em;
        letter-spacing: 1px;
    }
    .bitzy-total-cals {
        color: #6ecb63;
        font-size: 1.2rem;
        font-family: 'Quicksand', 'Montserrat', sans-serif;
        font-weight: bold;
        margin-bottom: 1em;
        letter-spacing: 1px;
    }
    </style>
    """, unsafe_allow_html=True)

    # st.markdown("""
    # <div class='bitzy-plot-box'>
    #     <div class='bitzy-plot-title'>📊 Track Your Macros by Meal Type</div>
    # </div>
    # """, unsafe_allow_html=True)

    macros_dropdown = st.selectbox('What do you want to track?', ('calories', 'protein', 'carbs', 'fat'))
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("Please log in to view your nutrition data.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    conn_user = create_user_connection(USER_DB)
    df = get_user_nutrition_data(conn_user, user_id)

    if df.empty:
        st.info("No data available for the selected macro.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    df['date'] = pd.to_datetime(df['date'])
    unique_dates = df['date'].dt.date.unique()
    if len(unique_dates) == 0:
        st.info("No entries found for any date.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    selected_date = st.selectbox("Select a date", options=unique_dates, format_func=lambda x: x.strftime('%Y-%m-%d'))
    df_day = df[df['date'].dt.date == selected_date]
    # --- Date selection ---

    if df_day.empty:
        st.info("No entries for this date.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # --- Group by meal type ---
    grouped_df = df_day.groupby('meal_type', as_index=False)[macros_dropdown].sum()
    grouped_df = grouped_df.sort_values('meal_type')

    # --- Total macro for the day ---
    total_macro = grouped_df[macros_dropdown].sum()
    # st.markdown(f"<div class='bitzy-total-cals'>Total {macros_dropdown.capitalize()} for {selected_date}: <span style='color:#ff96ec'>{total_macro}</span></div>", unsafe_allow_html=True)

    # --- Lollipop Chart for a more sophisticated look ---
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=grouped_df['meal_type'],
        y=grouped_df[macros_dropdown],
        mode='markers+lines+text',
        marker=dict(size=18, color='#ff96ec', line=dict(width=2, color='#fff6fb')),
        line=dict(color='#ff96ec', width=4),
        text=grouped_df[macros_dropdown],
        textposition='top center',
        hovertemplate=f"%{{x}}<br>{macros_dropdown.capitalize()}: %{{y}}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(
            text=f"{macros_dropdown.capitalize()} Intake by Meal Type ({selected_date})",
            x=0.5,
            xanchor='center'
        ),
        plot_bgcolor='#e4ffa6',
        paper_bgcolor='#e4ffa6',
        font=dict(
            family='Quicksand, Montserrat, Arial, sans-serif',
            size=15,
            color='black'
        ),
        xaxis_title="Meal Type",
        yaxis_title=f"{macros_dropdown.capitalize()}",
        showlegend=False,
        margin=dict(l=40, r=40, t=80, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)