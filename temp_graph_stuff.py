import numpy
import plotly.express as px
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from database.user_db import create_connection as create_user_connection, USER_DB
from database.user_db import parse_quantity


# creating the data visualizations

# Example: Calculate total calories
def calculate_total_calories(conn, user_id, start_date, end_date):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.calories, jd.quantity
        FROM JournalDish jd
        JOIN Journal j ON jd.journal_id = j.journal_id
        JOIN Dish d ON jd.dish_id = d.dish_id
        WHERE j.user_id = ? AND j.date BETWEEN ? AND ?
    """, (user_id, start_date, end_date))
    
    total_calories = 0
    for row in cursor.fetchall():
        calories = row[0] or 0
        quantity_str = row[1] or "1"
        
        # Convert quantity to numeric value
        if quantity_str == "1/3":
            quantity = 1/3
        elif quantity_str == "1/2":
            quantity = 0.5
        else:
            try:
                quantity = float(quantity_str)
            except ValueError:
                quantity = 1.0
                
        total_calories += calories * quantity
    
    return total_calories


# --- Update get_user_nutrition_data to include quantity ---
def get_user_nutrition_data(conn_user, user_id):
    sql = """
        SELECT
            dj.date,
            dj.meal_type,
            d.dish_name,
            jd.quantity, -- Fetch quantity
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

    # --- Calculate adjusted macros based on quantity ---
    if not df.empty:
        df['quantity_float'] = df['quantity'].apply(parse_quantity)
        for col in ['calories', 'protein', 'carbs', 'fat']:
            # Ensure column exists and is numeric before multiplying
            if col in df.columns:
                 # Fill NaN/None with 0 before multiplication
                 df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                 df[col] = df[col] * df['quantity_float']
            else:
                 df[col] = 0 # Add column as 0 if missing

    return df


# --- Update create_plots --
def create_plots():
    st.markdown("""
    <style>
    .bitzy-plot-box {
        background: #fff6fb;
        border-radius: 18px;
        padding: 1.5em;
        margin: 0 auto 2em auto;
        max-width: 800px;
        box-shadow: 0 2px 16px #ffd4f1;
        text-align: center;
    }
    .bitzy-plot-title {
        color: #ff96ec;
        font-size: 1.4rem;
        font-family: 'Quicksand', 'Montserrat', sans-serif;
        font-weight: bold;
        margin-bottom: 1em;
        letter-spacing: 1px;
    }
    .stSelectbox label, .stMultiSelect label {
         font-weight: bold !important;
         color: #272936 !important;
         font-size: 1.1em !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class='bitzy-plot-title' style="
        background: #ffffff;
        border-radius: 12px;
        padding: 1em;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
        display: inline-block;
    ">
        📊 Track Your Macros by Meal Type
    </div>
    """, unsafe_allow_html=True)

    macro_options = ['calories', 'protein', 'carbs', 'fat']
    selected_macros = st.multiselect(
        'Which macros do you want to track? (Choose 1 or more)',
        macro_options,
        default=['calories']
    )

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("Please log in to view your nutrition data.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    conn_user = None
    try:
        conn_user = create_user_connection(USER_DB)
        df = get_user_nutrition_data(conn_user, user_id)

        if df.empty:
            st.info("No journal data available to plot.")
            return

        df['date'] = pd.to_datetime(df['date'])
        unique_dates = sorted(df['date'].dt.date.unique(), reverse=True)
        if len(unique_dates) == 0:
            st.info("No entries found for any date.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        selected_date = st.selectbox("Select a date", options=unique_dates, format_func=lambda x: x.strftime('%Y-%m-%d'))
        df_day = df[df['date'].dt.date == selected_date].copy()

        if df_day.empty:
            st.info(f"No entries for {selected_date.strftime('%Y-%m-%d')}.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        # --- Group by meal type and sum selected macros ---
        grouped_df = df_day.groupby('meal_type', as_index=False)[selected_macros].sum()
        grouped_df = grouped_df.sort_values('meal_type')

        # --- Plot: Grouped Bar Chart ---
        fig = go.Figure()
        colors = ['#ff96ec', '#ffd4f1', '#a3e4db', '#f7cac9']  # Add more if needed

        for idx, macro in enumerate(selected_macros):
            fig.add_trace(go.Bar(
                x=grouped_df['meal_type'],
                y=grouped_df[macro],
                name=macro.capitalize(),
                marker_color=colors[idx % len(colors)],
                text=[f"{val:.0f}" for val in grouped_df[macro]],
                textposition='outside'
            ))

        fig.update_layout(
            barmode='group',
            title=dict(
                text=f"{', '.join([m.capitalize() for m in selected_macros])} Intake by Meal Type ({selected_date.strftime('%Y-%m-%d')})",
                x=0.5,
                xanchor='center',
                font=dict(size=18, color='#272936')
            ),
            plot_bgcolor='#fff6fb',
            paper_bgcolor='#fff6fb',
            font=dict(
                family='Quicksand, Montserrat, Arial, sans-serif',
                size=14,
                color='#272936'
            ),
            xaxis_title="Meal Type",
            yaxis_title="Amount",
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(gridcolor='#ffd4f1', zeroline=False),
            showlegend=True,
            margin=dict(l=50, r=20, t=80, b=50)
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error generating plot: {e}")
    finally:
        if conn_user:
            conn_user.close()
        st.markdown("</div>", unsafe_allow_html=True)


