import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from google.oauth2.service_account import Credentials
import gspread
import calendar

DC_RED = "#E61A27"
DC_SILVER = "#C0C0C0"
DC_DARK_SILVER = "#8A8A8A"
DC_BLACK = "#1A1A1A"
DC_WHITE = "#FFFFFF"
DC_LIGHT_GRAY = "#F5F5F5"

PERSON_COLORS = {
    "Cain": DC_RED,
    "Shiv": DC_DARK_SILVER
}

st.set_page_config(
    page_title="Diet Coke Tracker 2026",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<meta name="viewport" content="width=1200">
""", unsafe_allow_html=True)

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Open+Sans:wght@400;600;700&display=swap');
    
    .stApp {{
        background: linear-gradient(135deg, {DC_WHITE} 0%, {DC_LIGHT_GRAY} 100%);
    }}
    
    .main-header {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 4rem;
        color: {DC_RED};
        text-align: center;
        letter-spacing: 3px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0;
    }}
    
    .sub-header {{
        font-family: 'Open Sans', sans-serif;
        font-size: 1.2rem;
        color: {DC_DARK_SILVER};
        text-align: center;
        margin-top: -10px;
        font-style: italic;
    }}
    
    .section-header {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.2rem;
        color: {DC_BLACK};
        border-bottom: 3px solid {DC_RED};
        padding-bottom: 10px;
        margin-top: 40px;
        letter-spacing: 2px;
    }}
    
    .leader-card {{
        background: linear-gradient(145deg, {DC_RED}, #B31520);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(230, 26, 39, 0.3);
        color: white;
    }}
    
    .leader-label {{
        font-family: 'Open Sans', sans-serif;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 3px;
        opacity: 0.9;
    }}
    
    [data-testid="stPlotlyChart"] {{
        background: white;
        border-radius: 20px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }}
    
    .stButton > button {{
        background-color: {DC_RED};
        color: white;
        border-radius: 25px;
        padding: 10px 30px;
        font-family: 'Open Sans', sans-serif;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }}
    
    .stButton > button:hover {{
        background-color: #B31520;
        box-shadow: 0 5px 15px rgba(230, 26, 39, 0.4);
    }}
    
    div[data-testid="stMetricValue"] {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.2rem;
        color: {DC_BLACK};
    }}
    
    div[data-testid="stMetricLabel"] {{
        font-family: 'Open Sans', sans-serif;
        color: {DC_DARK_SILVER};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    [data-testid="stDataFrame"] {{
        background: white;
        border-radius: 20px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }}
</style>
""", unsafe_allow_html=True)

SHEET_ID = "1xEYXLgh2UeweXv44RipufxCM9uEc7xk9HpeJKkKdyPo"
SHEET_NAME = "Form Responses 1"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

@st.cache_data(ttl=300)
def load_data():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    column_mapping = {
        "Timestamp": "timestamp",
        "Who are you": "person",
        "DC or inferior product?": "drink_type",
        "DC or inferior produ": "drink_type",
        "Date & time": "datetime",
        "Format": "format",
        "Ounces": "ounces",
        "Additional notes?": "notes",
        "AM only: is this the first beverage you've had today?": "first_beverage",
        "AM only: is this the first beverage you've had": "first_beverage"
    }
    df.columns = [col.strip() for col in df.columns]
    for orig, new in column_mapping.items():
        for col in df.columns:
            if col.startswith(orig) or orig.startswith(col):
                df = df.rename(columns={col: new})
                break
    
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df["date"] = df["datetime"].dt.date
    df["hour"] = df["datetime"].dt.hour
    df["day_of_week"] = df["datetime"].dt.day_name()
    df["week"] = df["datetime"].dt.isocalendar().week
    df["month"] = df["datetime"].dt.month
    df["ounces"] = df["ounces"].astype(str).str.replace(r"[^\d.]", "", regex=True)
    df["ounces"] = pd.to_numeric(df["ounces"], errors="coerce").fillna(12)
    df["is_diet_coke"] = df["drink_type"].str.lower().str.contains("diet coke", na=False)
    
    return df

def get_person_color(person):
    return PERSON_COLORS.get(person, DC_DARK_SILVER)

def generate_heatmap_svg(df, person, person_color):
    person_df = df[df["person"] == person]
    daily_counts = person_df.groupby("date").size().to_dict()
    
    if daily_counts:
        max_count = max(daily_counts.values())
    else:
        max_count = 1
    
    cell_size = 6
    cell_gap = 2
    month_gap = 8
    month_labels = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    
    svg_parts = []
    x_offset = 0
    
    for month in range(1, 13):
        days_in_month = calendar.monthrange(2026, month)[1]
        first_day_weekday = calendar.monthrange(2026, month)[0]
        
        weeks_in_month = (days_in_month + first_day_weekday + 6) // 7
        month_width = weeks_in_month * (cell_size + cell_gap)
        
        svg_parts.append(f'<text x="{x_offset + month_width/2}" y="8" font-size="8" fill="#8A8A8A" text-anchor="middle" font-family="Open Sans, sans-serif">{month_labels[month-1]}</text>')
        
        day = 1
        for week in range(weeks_in_month):
            for weekday in range(7):
                if week == 0 and weekday < first_day_weekday:
                    continue
                if day > days_in_month:
                    break
                
                current_date = datetime(2026, month, day).date()
                count = daily_counts.get(current_date, 0)
                
                if count == 0:
                    fill = "#EBEDF0"
                else:
                    intensity = min(count / max(max_count, 1), 1.0)
                    if person_color == DC_RED:
                        r = int(235 + (230 - 235) * intensity)
                        g = int(237 + (26 - 237) * intensity)
                        b = int(240 + (39 - 240) * intensity)
                    else:
                        r = int(235 + (138 - 235) * intensity)
                        g = int(237 + (138 - 237) * intensity)
                        b = int(240 + (138 - 240) * intensity)
                    fill = f"rgb({r},{g},{b})"
                
                x = x_offset + week * (cell_size + cell_gap)
                y = 12 + weekday * (cell_size + cell_gap)
                
                svg_parts.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="1" fill="{fill}"/>')
                day += 1
        
        x_offset += month_width + month_gap
    
    total_width = x_offset - month_gap
    total_height = 12 + 7 * (cell_size + cell_gap)
    
    svg = f'<svg width="{total_width}" height="{total_height}" xmlns="http://www.w3.org/2000/svg">{"".join(svg_parts)}</svg>'
    return svg

def calculate_streaks(df, person):
    person_df = df[df["person"] == person].copy()
    if person_df.empty:
        return 0, 0
    
    dates_with_drinks = set(person_df["date"].dropna())
    if not dates_with_drinks:
        return 0, 0
    
    min_date = min(dates_with_drinks)
    max_date = max(dates_with_drinks)
    
    current_streak = 0
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    if today in dates_with_drinks:
        check_date = today
    else:
        check_date = yesterday
    
    while check_date >= min_date:
        if check_date in dates_with_drinks:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    longest_streak = 0
    temp_streak = 0
    check_date = min_date
    while check_date <= max_date:
        if check_date in dates_with_drinks:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0
        check_date += timedelta(days=1)
    
    return current_streak, longest_streak

def predict_year_end(df, person):
    person_df = df[df["person"] == person].copy()
    if person_df.empty:
        return 0, 0
    
    dates = person_df["date"].dropna()
    if len(dates) == 0:
        return 0, 0
    
    min_date = dates.min()
    max_date = dates.max()
    days_tracked = (max_date - min_date).days + 1
    
    if days_tracked == 0:
        return 0, 0
    
    total_drinks = len(person_df)
    total_ounces = person_df["ounces"].sum()
    
    daily_avg_drinks = total_drinks / days_tracked
    daily_avg_ounces = total_ounces / days_tracked
    
    year_end = datetime(2026, 12, 31).date()
    days_remaining = (year_end - max_date).days
    
    predicted_drinks = total_drinks + (daily_avg_drinks * days_remaining)
    predicted_ounces = total_ounces + (daily_avg_ounces * days_remaining)
    
    return int(predicted_drinks), int(predicted_ounces)

def get_fun_stats(df, person):
    person_df = df[df["person"] == person].copy()
    if person_df.empty:
        return {}
    
    daily_counts = person_df.groupby("date").size()
    daily_ounces = person_df.groupby("date")["ounces"].sum()
    
    stats = {
        "max_drinks_one_day": daily_counts.max() if len(daily_counts) > 0 else 0,
        "max_drinks_date": daily_counts.idxmax() if len(daily_counts) > 0 else None,
        "max_ounces_one_day": daily_ounces.max() if len(daily_ounces) > 0 else 0,
        "favorite_format": person_df["format"].mode().iloc[0] if len(person_df["format"].mode()) > 0 else "N/A",
        "favorite_hour": person_df["hour"].mode().iloc[0] if len(person_df["hour"].mode()) > 0 else None,
        "pct_diet_coke": (person_df["is_diet_coke"].sum() / len(person_df) * 100) if len(person_df) > 0 else 0,
        "first_beverage_pct": (person_df["first_beverage"].str.lower().str.contains("yes", na=False).sum() / len(person_df) * 100) if len(person_df) > 0 else 0
    }
    
    return stats

def style_chart(fig):
    fig.update_layout(
        font_family="Open Sans",
        title_font_family="Bebas Neue",
        title_font_size=24,
        title_font_color=DC_BLACK,
        paper_bgcolor="white",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=80, b=40),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=DC_SILVER,
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        xaxis=dict(
            gridcolor=DC_LIGHT_GRAY,
            linecolor=DC_SILVER
        ),
        yaxis=dict(
            gridcolor=DC_LIGHT_GRAY,
            linecolor=DC_SILVER
        )
    )
    return fig

df = load_data()
people = df["person"].unique().tolist()

st.markdown('<h1 class="main-header">DIET COKE TRACKER 2026</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Tracking the important things in life</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown('<h2 class="section-header">LEADERBOARD</h2>', unsafe_allow_html=True)

leaderboard = df.groupby("person").agg(
    total_drinks=("person", "size"),
    total_ounces=("ounces", "sum"),
    avg_daily_drinks=("date", lambda x: len(x) / x.nunique() if x.nunique() > 0 else 0)
).sort_values("total_drinks", ascending=False)

if len(leaderboard) >= 2:
    leader = leaderboard.index[0]
    second = leaderboard.index[1]
    lead_margin = int(leaderboard.loc[leader, "total_drinks"] - leaderboard.loc[second, "total_drinks"])
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, {DC_SILVER}, {DC_DARK_SILVER}); border-radius: 20px; padding: 25px; text-align: center; color: white; margin-top: 40px;">
            <p style="font-family: 'Open Sans'; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px;">Second Place</p>
            <p style="font-family: 'Bebas Neue'; font-size: 2.5rem; margin: 0;">{second}</p>
            <p style="font-family: 'Bebas Neue'; font-size: 1.8rem; margin: 5px 0;">{int(leaderboard.loc[second, 'total_drinks'])} drinks</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="leader-card">
            <p class="leader-label">Current Leader</p>
            <p style="font-family: 'Bebas Neue'; font-size: 2.5rem; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">{leader}</p>
            <p style="font-family: 'Bebas Neue'; font-size: 2.5rem; margin: 10px 0;">{int(leaderboard.loc[leader, 'total_drinks'])} DRINKS</p>
            <p style="font-family: 'Open Sans'; font-size: 1rem;">Leading by {lead_margin} drink{"s" if lead_margin != 1 else ""}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_drinks = int(leaderboard["total_drinks"].sum())
        total_ounces = int(leaderboard["total_ounces"].sum())
        
        st.markdown(f"""
        <div style="background: white; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-top: 40px;">
            <p style="font-family: 'Open Sans'; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; color: {DC_DARK_SILVER};">Combined Stats</p>
            <p style="font-family: 'Bebas Neue'; font-size: 2rem; color: {DC_BLACK}; margin: 5px 0;">{total_drinks} drinks</p>
            <p style="font-family: 'Bebas Neue'; font-size: 1.5rem; color: {DC_DARK_SILVER}; margin: 0;">{total_ounces:,} oz</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<h2 class="section-header">TRENDS</h2>', unsafe_allow_html=True)

daily_trends = df.groupby(["date", "person"]).agg(
    drinks=("person", "size"),
    ounces=("ounces", "sum")
).reset_index()

fig_drinks = px.line(
    daily_trends,
    x="date",
    y="drinks",
    color="person",
    title="DAILY DRINK COUNT",
    markers=True,
    color_discrete_map=PERSON_COLORS
)
fig_drinks.update_traces(line=dict(width=3), marker=dict(size=10))
fig_drinks = style_chart(fig_drinks)
fig_drinks.update_layout(xaxis_title="", yaxis_title="Drinks")
st.plotly_chart(fig_drinks, use_container_width=True)

cumulative = df.sort_values("datetime").copy()
cumulative["cumulative_ounces"] = cumulative.groupby("person")["ounces"].cumsum()

fig_cumulative = px.line(
    cumulative,
    x="datetime",
    y="cumulative_ounces",
    color="person",
    title="THE RACE TO 5000 OUNCES",
    color_discrete_map=PERSON_COLORS
)
fig_cumulative.update_traces(line=dict(width=4))
fig_cumulative.add_hline(y=5000, line_dash="dash", line_color=DC_SILVER, annotation_text="5000 oz Goal")
fig_cumulative = style_chart(fig_cumulative)
fig_cumulative.update_layout(xaxis_title="", yaxis_title="Total Ounces")
st.plotly_chart(fig_cumulative, use_container_width=True)

st.markdown('<h2 class="section-header">CONSUMPTION PATTERNS</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    hourly = df.groupby(["hour", "person"]).size().reset_index(name="count")
    fig_hourly = px.bar(
        hourly,
        x="hour",
        y="count",
        color="person",
        barmode="group",
        title="DRINKS BY HOUR",
        color_discrete_map=PERSON_COLORS
    )
    fig_hourly = style_chart(fig_hourly)
    fig_hourly.update_layout(xaxis_title="Hour of Day", yaxis_title="Count")
    st.plotly_chart(fig_hourly, use_container_width=True)

with col2:
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    daily = df.groupby(["day_of_week", "person"]).size().reset_index(name="count")
    daily["day_of_week"] = pd.Categorical(daily["day_of_week"], categories=day_order, ordered=True)
    daily = daily.sort_values("day_of_week")
    fig_daily = px.bar(
        daily,
        x="day_of_week",
        y="count",
        color="person",
        barmode="group",
        title="DRINKS BY DAY OF WEEK",
        color_discrete_map=PERSON_COLORS
    )
    fig_daily = style_chart(fig_daily)
    fig_daily.update_layout(xaxis_title="", yaxis_title="Count")
    st.plotly_chart(fig_daily, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    format_counts = df.groupby(["format", "person"]).size().reset_index(name="count")
    fig_format = px.bar(
        format_counts,
        x="count",
        y="format",
        color="person",
        barmode="group",
        title="DRINKS BY FORMAT",
        orientation="h",
        color_discrete_map=PERSON_COLORS
    )
    fig_format = style_chart(fig_format)
    fig_format.update_layout(xaxis_title="Count", yaxis_title="")
    st.plotly_chart(fig_format, use_container_width=True)

with col2:
    drink_type_counts = df.groupby(["drink_type", "person"]).size().reset_index(name="count")
    fig_type = px.bar(
        drink_type_counts,
        x="count",
        y="drink_type",
        color="person",
        barmode="group",
        title="DC VS INFERIOR PRODUCTS",
        orientation="h",
        color_discrete_map=PERSON_COLORS
    )
    fig_type = style_chart(fig_type)
    fig_type.update_layout(xaxis_title="Count", yaxis_title="")
    st.plotly_chart(fig_type, use_container_width=True)

st.markdown('<h2 class="section-header">PLAYER STATS</h2>', unsafe_allow_html=True)

for person in people:
    person_df = df[df["person"] == person]
    current_streak, longest_streak = calculate_streaks(df, person)
    predicted_drinks, predicted_ounces = predict_year_end(df, person)
    fun_stats = get_fun_stats(df, person)
    days_active = person_df["date"].nunique()
    avg_daily = len(person_df) / days_active if days_active > 0 else 0
    
    person_color = get_person_color(person)
    
    max_day = fun_stats.get("max_drinks_one_day", 0)
    max_date = fun_stats.get("max_drinks_date")
    max_date_str = max_date.strftime("%m/%d") if max_date else ""
    loyalty = fun_stats.get("pct_diet_coke", 0)
    hour = fun_stats.get("favorite_hour")
    peak_hour_str = f"{hour % 12 or 12} {'AM' if hour < 12 else 'PM'}" if hour is not None else "N/A"
    
    heatmap_svg = generate_heatmap_svg(df, person, person_color)
    
    st.markdown(f"""
    <div style="background: white; border-radius: 20px; padding: 25px 30px; margin: 20px 0; box-shadow: 0 8px 25px rgba(0,0,0,0.1); border-top: 5px solid {person_color}; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
        <h3 style="font-family: 'Bebas Neue'; font-size: 2.5rem; color: {person_color}; margin: 0; flex-shrink: 0;">{person.upper()}</h3>
        <div style="flex: 1; display: flex; justify-content: center; align-items: center; min-width: 300px;">
            {heatmap_svg}
        </div>
        <div style="display: flex; gap: 30px; flex-wrap: wrap; flex-shrink: 0;">
            <div style="text-align: center;">
                <span style="font-family: 'Open Sans'; font-size: 0.75rem; color: #8A8A8A; text-transform: uppercase; letter-spacing: 1px;">Max in One Day</span><br>
                <span style="font-family: 'Bebas Neue'; font-size: 1.5rem; color: #1A1A1A;">{max_day}</span>
                <span style="font-family: 'Open Sans'; font-size: 0.8rem; color: #8A8A8A;"> ({max_date_str})</span>
            </div>
            <div style="text-align: center;">
                <span style="font-family: 'Open Sans'; font-size: 0.75rem; color: #8A8A8A; text-transform: uppercase; letter-spacing: 1px;">DC Loyalty</span><br>
                <span style="font-family: 'Bebas Neue'; font-size: 1.5rem; color: {DC_RED};">{loyalty:.0f}%</span>
            </div>
            <div style="text-align: center;">
                <span style="font-family: 'Open Sans'; font-size: 0.75rem; color: #8A8A8A; text-transform: uppercase; letter-spacing: 1px;">Peak Hour</span><br>
                <span style="font-family: 'Bebas Neue'; font-size: 1.5rem; color: #1A1A1A;">{peak_hour_str}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Drinks", len(person_df))
    with col2:
        st.metric("Days Active", days_active)
    with col3:
        st.metric("Current Streak", f"{current_streak} days")
    with col4:
        st.metric("Predicted Year-End", f"{predicted_drinks:,}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Ounces", f"{person_df['ounces'].sum():,.0f}")
    with col2:
        st.metric("Avg Drinks/Day", f"{avg_daily:.1f}")
    with col3:
        st.metric("Longest Streak", f"{longest_streak} days")
    with col4:
        st.metric("Predicted Ounces", f"{predicted_ounces:,}")
    
    st.markdown("---")

st.markdown('<h2 class="section-header">RECENT ACTIVITY</h2>', unsafe_allow_html=True)

recent = df.sort_values("datetime", ascending=False).head(15)
recent_display = recent[["datetime", "person", "drink_type", "format", "ounces", "notes"]].copy()
recent_display["datetime"] = recent_display["datetime"].dt.strftime("%m/%d/%Y %I:%M %p")
recent_display.columns = ["When", "Who", "What", "Format", "Oz", "Notes"]

st.dataframe(
    recent_display,
    use_container_width=True,
    hide_index=True
)

st.markdown(f"""
<div style="text-align: center; padding: 40px; color: {DC_DARK_SILVER}; font-family: 'Open Sans';">
    <p>Made with caffeine and questionable life choices</p>
</div>
""", unsafe_allow_html=True)
