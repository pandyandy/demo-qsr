# streamlit_app.py
import streamlit as st
import pandas as pd
import duckdb
from streamlit_option_menu import option_menu

from scripts.about import introduction
from scripts.locations import locations
from scripts.overview import overview
from scripts.ai_analysis import ai_analysis
from scripts.support import support
from scripts.openai import assistant
from scripts.sapi import read_data
from scripts.viz import metrics
from scripts.db_utils import get_db_connection

st.set_page_config(layout="wide")

# Load secrets
ASSISTANT_ID = st.secrets['ASSISTANT_ID']
FILE_ID = st.secrets['FILE_ID']
LOGO_URL = st.secrets['LOGO_URL']

# Initialize session state variables
session_defaults = {
    "thread_id": None,
    "messages": [{'role': 'assistant', 'content': 'Welcome! How can I assist you today?'}],
    "new_prompt": None,
    "instruction": '',
    "regenerate_clicked": False,
    "generated_responses": {},
    "filtered_locations": pd.DataFrame(),
    "location_count_total": None,
    "review_count_total": None,
    "avg_rating_total": None,
    "data_collected_at": None
}

for key, value in session_defaults.items():
    st.session_state.setdefault(key, value)

# Define menu options and icons
options = ['About', 'Locations', 'Overview', 'AI Analysis', 'Support', 'Assistant']
icons = ['info-circle', 'pin-map-fill', 'people', 'file-bar-graph', 'chat-heart', 'robot']

menu_id = option_menu(None, options=options, icons=icons, key='menu_id', orientation="horizontal")

# Load data
locations_data = pd.read_csv(st.secrets['locations_path'])
reviews_data = read_data(st.secrets['reviews_path'])
reviews_path = f"{st.secrets['reviews_path'].split('.')[-1]}.csv"

# Connect to DuckDB
db = get_db_connection()

# Create tables in DuckDB
db.execute(f"CREATE TABLE IF NOT EXISTS locations AS SELECT * FROM read_csv_auto('{st.secrets['locations_path']}');")
db.execute(f"CREATE OR REPLACE TABLE reviews AS SELECT * FROM read_csv_auto('{reviews_path}');")
db.execute(f"CREATE TABLE IF NOT EXISTS sentences AS SELECT * FROM read_csv_auto('{st.secrets['sentences_path']}');")
db.execute(f"CREATE TABLE IF NOT EXISTS attributes AS SELECT * FROM read_csv_auto('{st.secrets['attributes_path']}');")

# Clean attributes data
db.execute("""
    UPDATE attributes 
    SET entity = 'burger' 
    WHERE entity = 'burgers';
    DELETE FROM attributes 
    WHERE entity IN ('i', 'you', 'she', 'he', 'it', 'we', 'they', 
                     'I', 'You', 'She', 'He', 'It', 'We', 'They', 
                     'whataburger', 'Whataburger')
""")

# Filter attributes
db.execute("""
    CREATE TABLE IF NOT EXISTS filtered_attributes AS 
    SELECT entity, attribute, SUM(count) AS count 
    FROM attributes 
    GROUP BY entity, attribute 
    HAVING SUM(count) > 2;
""")

# Display logo in sidebar
st.sidebar.markdown(
    f'''
        <div style="text-align: center; margin-top: 20px; margin-bottom: 40px;">
            <img src="{LOGO_URL}" alt="Logo" width="200">
        </div>
    ''',
    unsafe_allow_html=True
)

# Brand Selection
if 'brand_options' not in st.session_state:
    st.session_state.brand_options = locations_data['BRAND'].unique().tolist()

brand = st.sidebar.selectbox('Select a brand', st.session_state.brand_options, index=0, placeholder='All', key='selected_brand') if st.secrets.get('all_brands', 'True') == 'True' else st.secrets['brand_filter']
st.session_state.filtered_locations = locations_data[locations_data['BRAND'] == brand]

# State Selection
state_options = sorted(st.session_state.filtered_locations['STATE'].unique().tolist())
selected_state = st.sidebar.multiselect('Select a state', state_options, placeholder='All') or state_options

# City Selection
city_options = sorted(st.session_state.filtered_locations[st.session_state.filtered_locations['STATE'].isin(selected_state)]['CITY'].unique().tolist())
city = st.sidebar.multiselect('Select a city', city_options, placeholder='All')
if len(city) > 0:
    selected_city = city
    location_options = sorted(st.session_state.filtered_locations[st.session_state.filtered_locations['CITY'].isin(selected_city)]['ADDRESS'].unique().tolist())
else:
    selected_city = city_options
    location_options = sorted(st.session_state.filtered_locations[st.session_state.filtered_locations['STATE'].isin(selected_state)]['ADDRESS'].unique().tolist())

# Location Selection
selected_location = st.sidebar.multiselect('Select a location', location_options, placeholder='All') or location_options

# Merge locations, reviews, and sentences data with brand filter
db.execute("""
    CREATE OR REPLACE TABLE locations_reviews_merged AS 
    SELECT l.*, r.*
    FROM locations l 
    INNER JOIN reviews r ON l.PLACE_ID = r.PLACE_ID
    WHERE l.BRAND = ?;
    """, (brand,))
    #       """, s.ENTITY, s.CATEGORY, s.CATEGORY_GROUP, s.TOPIC
#    LEFT JOIN (
 #       SELECT REVIEW_ID,
  #          ARRAY_AGG(DISTINCT ENTITY) AS ENTITY,
   #         ARRAY_AGG(DISTINCT CASE WHEN CATEGORY != 'Unknown' AND CATEGORY IS NOT NULL AND CATEGORY != '' THEN CATEGORY END) AS CATEGORY,
    #        ARRAY_AGG(DISTINCT CASE WHEN CATEGORY_GROUP != 'Unknown' AND CATEGORY_GROUP IS NOT NULL AND CATEGORY_GROUP != '' THEN CATEGORY_GROUP END) AS CATEGORY_GROUP,
     #       ARRAY_AGG(DISTINCT CASE WHEN TOPIC != 'Unknown' AND TOPIC IS NOT NULL AND TOPIC != '' THEN TOPIC END) AS TOPIC
      #  FROM sentences
       # GROUP BY REVIEW_ID
    #) AS s ON r.REVIEW_ID = s.REVIEW_ID
    
# Sentiment Selection
sentiment_options = sorted(db.execute("SELECT DISTINCT OVERALL_SENTIMENT FROM locations_reviews_merged").fetchdf()['OVERALL_SENTIMENT'].tolist())
selected_sentiment = st.sidebar.multiselect('Select a sentiment', sentiment_options, placeholder='All') or sentiment_options

# Rating Selection
rating_options = sorted(db.execute("SELECT DISTINCT RATING FROM locations_reviews_merged").fetchdf()['RATING'].tolist())
selected_rating = st.sidebar.multiselect('Select a review rating', rating_options, placeholder='All') or rating_options

# Date Selection
date_options = ['Last Week', 'Last Month', 'Last 3 Months', 'All Time', 'Other']
date_selection = st.sidebar.selectbox('Select a date', date_options, index=None, placeholder='All')

min_date = db.execute("SELECT MIN(REVIEW_DATE) FROM locations_reviews_merged").fetchone()[0]
max_date = db.execute("SELECT MAX(REVIEW_DATE) FROM locations_reviews_merged").fetchone()[0]

if date_selection == 'Other':
    start_date, end_date = st.sidebar.slider('Select date range', value=[min_date.date(), max_date.date()], min_value=min_date.date(), max_value=max_date.date(), key='date_input')
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date).replace(hour=23, minute=59)
else:
    end_date = pd.to_datetime('today')
    start_date = {
        'Last Week': end_date - pd.DateOffset(weeks=1),
        'Last Month': end_date - pd.DateOffset(months=1),
        'Last 3 Months': end_date - pd.DateOffset(months=3),
        'All Time': min_date
    }.get(date_selection, min_date)

selected_date_range = (start_date, end_date)

# Fetch counts and data
st.session_state.location_count_total = db.execute("SELECT COUNT(DISTINCT PLACE_ID) FROM locations_reviews_merged;").fetchone()[0]
st.session_state.review_count_total = db.execute("SELECT COUNT(DISTINCT REVIEW_ID) FROM locations_reviews_merged;").fetchone()[0]
st.session_state.avg_rating_total = db.execute("SELECT AVG(RATING) FROM locations_reviews_merged;").fetchone()[0]
st.session_state.data_collected_at = db.execute("SELECT MAX(DATA_COLLECTED_AT) FROM locations_reviews_merged;").fetchone()[0]

# Filter data based on selected filters
query = """
    SELECT *
    FROM locations_reviews_merged
    WHERE STATE IN ? 
    AND CITY IN ? 
    AND ADDRESS IN ? 
    AND OVERALL_SENTIMENT IN ? 
    AND RATING IN ?
    AND REVIEW_DATE BETWEEN ? AND ?
    ORDER BY REVIEW_DATE DESC
"""
filtered_data = db.execute(
    query,
    [selected_state, selected_city, selected_location, selected_sentiment, selected_rating, start_date, end_date]
).fetchdf()

# Check for empty data
if filtered_data.empty:
    st.info('No data available for the selected filters.', icon=':material/info:')
    st.stop()

st.sidebar.divider()
st.sidebar.caption(f"**Data last updated on:** {st.session_state.data_collected_at}.")

## TABS
if menu_id == 'About':
    introduction()
    
if menu_id == 'Locations':    
    metrics(st.session_state.location_count_total, st.session_state.review_count_total, st.session_state.avg_rating_total, filtered_data)
    locations(filtered_data)

if menu_id == 'Overview':
    metrics(st.session_state.location_count_total, st.session_state.review_count_total, st.session_state.avg_rating_total, filtered_data)
    overview(filtered_data)

if menu_id == 'AI Analysis':
    metrics(st.session_state.location_count_total, st.session_state.review_count_total, st.session_state.avg_rating_total, filtered_data, show_pie=True)
    ai_analysis(filtered_data)

if menu_id == 'Support':
    support(filtered_data, reviews_data)

if menu_id == 'Assistant':
    assistant(file_id=st.secrets['FILE_ID'], assistant_id=st.secrets['ASSISTANT_ID']) #, bot_data=bot_data)

