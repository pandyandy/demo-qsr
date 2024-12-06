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

st.set_page_config(layout="wide")

ASSISTANT_ID=st.secrets['ASSISTANT_ID']
FILE_ID=st.secrets['FILE_ID']
LOGO_URL=st.secrets['LOGO_URL']

# Initialize session state variables
session_defaults = {
    "thread_id": None,
    "messages": [{'role': 'assistant', 'content': 'Welcome! How can I assist you today?'}],
#    "table_written": False,
    "new_prompt": None,
    "instruction": '',
    "regenerate_clicked": False,
    "generated_responses": {}
}
for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

options = ['About', 'Locations', 'Overview', 'AI Analysis', 'Support', 'Assistant']
icons=['info-circle', 'pin-map-fill', 'people', 'file-bar-graph', 'chat-heart', 'robot']

menu_id = option_menu(None, options=options, icons=icons, key='menu_id', orientation="horizontal")

locations_data = pd.read_csv(st.secrets['locations_path'])
reviews_data = read_data(st.secrets['reviews_path'])
reviews_path = 'ALL_BRANDS_REVIEWS.csv'
#sentences_data = pd.read_csv(st.secrets['sentences_path'])
#attributes = pd.read_csv(st.secrets['attributes_path'])
#bot_data = pd.read_csv(st.secrets['bot_path'])

db = duckdb.connect(database=':memory:')
db.execute(f"CREATE TABLE locations AS SELECT * FROM read_csv_auto('{st.secrets['locations_path']}');")
db.execute(f"CREATE TABLE reviews AS SELECT * FROM read_csv_auto('{reviews_path}');")
db.execute(f"CREATE TABLE sentences AS SELECT * FROM read_csv_auto('{st.secrets['sentences_path']}');")
db.execute(f"CREATE TABLE attributes AS SELECT * FROM read_csv_auto('{st.secrets['attributes_path']}');")

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

db.execute("""
    CREATE TABLE filtered_attributes AS 
    SELECT entity, attribute, SUM(count) AS count 
    FROM attributes 
    GROUP BY entity, attribute 
    HAVING SUM(count) > 2;
""")

#attributes['entity'] = attributes['entity'].replace('burgers', 'burger')
#pronouns_to_remove = ['i', 'you', 'she', 'he', 'it', 'we', 'they', 'I', 'You', 'She', 'He', 'It', 'We', 'They', 'whataburger', 'Whataburger']
#attributes = attributes[~attributes['entity'].isin(pronouns_to_remove)]
#attributes = attributes.groupby(['entity', 'attribute'])['count'].sum().reset_index()
#attributes = attributes[attributes['count'] > 2]

## LOGO
st.sidebar.markdown(
    f'''
        <div style="text-align: center; margin-top: 20px; margin-bottom: 40px;">
            <img src="{LOGO_URL}" alt="Logo" width="200">
        </div>
    ''',
    unsafe_allow_html=True
)

# Merge locations and reviews data once and save to session state
#if 'locations_reviews_merged' not in st.session_state:
#    st.session_state['locations_reviews_merged'] = pd.merge(locations_data, reviews_data, on='PLACE_ID', how='inner')

#locations_reviews_merged = st.session_state['locations_reviews_merged']

# if 'all_data_merged' not in st.session_state:
#     st.session_state['all_data_merged'] = locations_reviews_merged.merge(
#         sentences_data.groupby('REVIEW_ID').agg(
#             ENTITY=('ENTITY', lambda x: [entity for entity in x if entity and pd.notna(entity)]),
#             CATEGORY=('CATEGORY', lambda x: x.unique().tolist()),
#             CATEGORY_GROUP=('CATEGORY_GROUP', lambda x: x.unique().tolist()),
#             TOPIC=('TOPIC', lambda x: x.unique().tolist())
#         ).reset_index(),
#         on='REVIEW_ID',
#         how='left'
#     )
# all_data_merged = st.session_state['all_data_merged']

## FILTERS
# Brand Selection
brand_options = locations_data['BRAND'].unique().tolist()
if st.secrets.get('all_brands', 'True') == 'True':
    #brand_options = db.execute("SELECT DISTINCT BRAND FROM locations;").fetchdf()['BRAND'].tolist()
    brand = st.sidebar.selectbox('Select a brand', brand_options, index=0, placeholder='All')#
else:
   brand = st.secrets['brand_filter']
#brand_options = db.execute("SELECT DISTINCT BRAND FROM locations_reviews_merged;").fetchdf()['BRAND'].tolist()
#brand = st.sidebar.selectbox('Select a brand', brand_options, index=0, placeholder='All')


#locations_reviews_filtered = db.execute("SELECT * FROM locations WHERE BRAND = ?", (brand,)).fetchdf()


# Merge locations, reviews, and sentences data in one step with brand filter
db.execute("""
    CREATE TABLE locations_reviews_sentences_merged AS 
    SELECT l.*, r.*, s.ENTITY, s.CATEGORY, s.CATEGORY_GROUP, s.TOPIC
    FROM locations l 
    INNER JOIN reviews r ON l.PLACE_ID = r.PLACE_ID
    LEFT JOIN (
        SELECT REVIEW_ID,
            ARRAY_AGG(DISTINCT ENTITY) AS ENTITY,
            ARRAY_AGG(DISTINCT CASE WHEN CATEGORY != 'Unknown' AND CATEGORY IS NOT NULL AND CATEGORY != '' THEN CATEGORY END) AS CATEGORY,
            ARRAY_AGG(DISTINCT CASE WHEN CATEGORY_GROUP != 'Unknown' AND CATEGORY_GROUP IS NOT NULL AND CATEGORY_GROUP != '' THEN CATEGORY_GROUP END) AS CATEGORY_GROUP,
            ARRAY_AGG(DISTINCT CASE WHEN TOPIC != 'Unknown' AND TOPIC IS NOT NULL AND TOPIC != '' THEN TOPIC END) AS TOPIC
        FROM sentences
        GROUP BY REVIEW_ID
    ) AS s ON r.REVIEW_ID = s.REVIEW_ID
    WHERE l.BRAND = ?;
""", (brand,))

#locations_reviews_merged = db.execute("SELECT * FROM locations_reviews_sentences_merged").fetchdf()
#st.write(locations_reviews_merged)
#locations_reviews_merged = locations_reviews_merged[locations_reviews_merged['BRAND'] == brand]

location_count_total = db.execute("SELECT COUNT(*) FROM locations_reviews_sentences_merged;").fetchone()[0]
review_count_total = db.execute("SELECT COUNT(*) FROM locations_reviews_sentences_merged WHERE BRAND = ?", (brand,)).fetchone()[0]
avg_rating_total = db.execute("SELECT AVG(RATING) FROM locations_reviews_sentences_merged").fetchone()[0]

data_collected_at = db.execute("SELECT MAX(DATA_COLLECTED_AT) FROM locations_reviews_sentences_merged;").fetchone()[0]


# State Selection
state_options = sorted(db.execute("SELECT DISTINCT STATE FROM locations_reviews_sentences_merged").fetchdf()['STATE'].tolist())
state = st.sidebar.multiselect('Select a state', state_options, placeholder='All')
if len(state) > 0:
    selected_state = state
else:
    selected_state = state_options

# City Selection
#city_options = sorted(locations_reviews_merged['CITY'].unique().tolist())
city_options = sorted(db.execute("SELECT DISTINCT CITY FROM locations_reviews_sentences_merged WHERE STATE IN ({})".format(','.join(['?'] * len(selected_state))), selected_state).fetchdf()['CITY'].tolist())
city = st.sidebar.multiselect('Select a city', city_options, placeholder='All')
if len(city) > 0:
    selected_city = city
    location_options = sorted(db.execute("SELECT DISTINCT ADDRESS FROM locations_reviews_sentences_merged WHERE CITY IN ({})".format(','.join(['?'] * len(selected_city))), selected_city).fetchdf()['ADDRESS'].tolist())
else:
    selected_city = city_options
    location_options = sorted(db.execute("SELECT DISTINCT ADDRESS FROM locations_reviews_sentences_merged WHERE STATE IN ({})".format(','.join(['?'] * len(selected_state))), selected_state).fetchdf()['ADDRESS'].tolist())

# Location Selection
location = st.sidebar.multiselect('Select a location', location_options, placeholder='All')
if len(location) > 0:
    selected_location = location
else:
    selected_location = location_options

# Filter reviews based on selected locations
#filtered_reviews = reviews_data[reviews_data['PLACE_ID'].isin(locations_data['PLACE_ID'])]

# Sentiment Selection
sentiment_options = sorted(db.execute("SELECT DISTINCT OVERALL_SENTIMENT FROM locations_reviews_sentences_merged").fetchdf()['OVERALL_SENTIMENT'].tolist())
sentiment = st.sidebar.multiselect('Select a sentiment', sentiment_options, placeholder='All')
if len(sentiment) > 0:
    selected_sentiment = sentiment
else:
    selected_sentiment = sentiment_options

# Rating Selection
rating_options = sorted(db.execute("SELECT DISTINCT RATING FROM locations_reviews_sentences_merged").fetchdf()['RATING'].tolist())
rating = st.sidebar.multiselect('Select a review rating', rating_options, placeholder='All')
if len(rating) > 0:
    selected_rating = rating
else:
    selected_rating = rating_options

# Date Selection
date_options = ['Last Week', 'Last Month', 'Last 3 Months', 'All Time', 'Other']
date_selection = st.sidebar.selectbox('Select a date', date_options, index=None, placeholder='All')
min_date = db.execute("SELECT MIN(REVIEW_DATE) FROM locations_reviews_sentences_merged").fetchone()[0]
max_date = db.execute("SELECT MAX(REVIEW_DATE) FROM locations_reviews_sentences_merged").fetchone()[0]

if date_selection is None:
    start_date = min_date
    end_date = max_date
elif date_selection == 'Other':
    start_date, end_date = st.sidebar.slider('Select date range', value=[min_date.date(), max_date.date()], min_value=min_date.date(), max_value=max_date.date(), key='date_input')
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date).replace(hour=23, minute=59)
else:
    end_date = pd.to_datetime('today')
    if date_selection == 'Last Week':
        start_date = end_date - pd.DateOffset(weeks=1)
    elif date_selection == 'Last Month':
        start_date = end_date - pd.DateOffset(months=1)
    elif date_selection == 'Last 3 Months':
        start_date = end_date - pd.DateOffset(months=3)
    elif date_selection == 'All Time':
        start_date = min_date
selected_date_range = (start_date, end_date)

# Add selected date range to the query
query = """
    SELECT *
    FROM locations_reviews_sentences_merged
    WHERE STATE IN ? 
    AND CITY IN ? 
    AND ADDRESS IN ? 
    AND OVERALL_SENTIMENT IN ? 
    AND RATING IN ?
    AND REVIEW_DATE BETWEEN ? AND ?
"""

locations_reviews_sentences_merged = db.execute(
    query,
    [selected_state, selected_city, selected_location, selected_sentiment, selected_rating, start_date, end_date]
).fetchdf()

attributes = db.execute("SELECT * FROM filtered_attributes").fetchdf()
#st.write(locations_reviews_merged)

# Convert REVIEW_DATE to datetime for comparison
#locations_reviews_merged['REVIEW_DATE'] = pd.to_datetime(locations_reviews_merged['REVIEW_DATE'])
#locations_reviews_merged = locations_reviews_merged[locations_reviews_merged['REVIEW_DATE'].between(selected_date_range[0], selected_date_range[1])]

#filtered_locations_with_reviews = locations_reviews_merged.merge(locations_data, on='PLACE_ID', how='inner')
sentences_data_filtered = db.execute("SELECT * FROM sentences WHERE REVIEW_ID IN (SELECT REVIEW_ID FROM locations_reviews_sentences_merged)").fetchdf()

if locations_reviews_sentences_merged.empty:
    st.info('No data available for the selected filters.', icon=':material/info:')
    st.stop()

st.sidebar.divider()
st.sidebar.caption(f"**Data last updated on:** {data_collected_at}.")

## TABS
if menu_id == 'About':
    introduction()
    
if menu_id == 'Locations':    
    metrics(location_count_total, review_count_total, avg_rating_total, locations_reviews_sentences_merged)
    locations(locations_reviews_sentences_merged)

if menu_id == 'Overview':
    metrics(location_count_total, review_count_total, avg_rating_total, locations_reviews_sentences_merged)
    overview(locations_reviews_sentences_merged)

if menu_id == 'AI Analysis':
    metrics(location_count_total, review_count_total, avg_rating_total, locations_reviews_sentences_merged, show_pie=True)
    ai_analysis(locations_reviews_sentences_merged, attributes, sentences_data_filtered)

if menu_id == 'Support':
    support(locations_reviews_sentences_merged, reviews_data)

if menu_id == 'Assistant':
    assistant(file_id=st.secrets['FILE_ID'], assistant_id=st.secrets['ASSISTANT_ID']) #, bot_data=bot_data)