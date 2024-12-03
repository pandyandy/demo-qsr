# streamlit_app.py
import streamlit as st
import pandas as pd

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

if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = [{'role': 'assistant', 'content': 'Welcome! How can I assist you today?'}]
if 'table_written' not in st.session_state:
    st.session_state.table_written = False
if 'new_prompt' not in st.session_state:
    st.session_state.new_prompt = None
if 'instruction' not in st.session_state:
    st.session_state.instruction = ''
if 'regenerate_clicked' not in st.session_state:
    st.session_state.regenerate_clicked = False
if 'generated_responses' not in st.session_state:
    st.session_state['generated_responses'] = {}

options = ['About', 'Locations', 'Overview', 'AI Analysis', 'Support', 'Assistant']
icons=['info-circle', 'pin-map-fill', 'people', 'file-bar-graph', 'chat-heart', 'robot']

menu_id = option_menu(None, options=options, icons=icons, key='menu_id', orientation="horizontal")

locations_data = pd.read_csv(st.secrets['locations_path']) #read_data('out.c-257-qsr-demo.LOCATIONS') #('/data/in/tables/location_review.csv')
reviews_data = read_data(st.secrets['reviews_path'])
sentences_data = pd.read_csv(st.secrets['sentences_path']) #read_data('out.c-257-qsr-demo.REVIEW_SENTENCE')
entities_data = pd.read_csv(st.secrets['entities_path']) #read_data('out.c-257-qsr-demo.REVIEW_ENTITY')
attributes = pd.read_csv(st.secrets['attributes_path']) #'entity_attribute_counts.csv') #'/data/in/tables/relations.csv')
bot_data = pd.read_csv(st.secrets['bot_path'])

attributes['entity'] = attributes['entity'].replace('burgers', 'burger')
pronouns_to_remove = ['i', 'you', 'she', 'he', 'it', 'we', 'they', 'I', 'You', 'She', 'He', 'It', 'We', 'They', 'whataburger', 'Whataburger']
attributes = attributes[~attributes['entity'].isin(pronouns_to_remove)]
attributes = attributes.groupby(['entity', 'attribute'])['count'].sum().reset_index()
attributes = attributes[attributes['count'] > 2]

## LOGO
st.sidebar.markdown(
    f'''
        <div style="text-align: center; margin-top: 20px; margin-bottom: 40px;">
            <img src="{LOGO_URL}" alt="Logo" width="200">
        </div>
    ''',
    unsafe_allow_html=True
)

## FILTERS
# Brand Selection
brand_options = locations_data['BRAND'].unique().tolist()
brand = st.sidebar.selectbox('Select a brand', brand_options, index=0, placeholder='All')
locations_data = locations_data[locations_data['BRAND'] == brand]
location_count_total = len(locations_data)
data_collected_at = locations_data['DATA_COLLECTED_AT'].max()

# Merge locations and reviews data and get the count of reviews data based on selected brand
merged_data = pd.merge(locations_data, reviews_data, on='PLACE_ID', how='inner')
review_count_total = len(merged_data[merged_data['BRAND'] == brand])
avg_rating_total = merged_data['RATING'].mean().round(2)

# State Selection
state_options = sorted(locations_data['STATE'].unique().tolist())
state = st.sidebar.multiselect('Select a state', state_options, placeholder='All')
if len(state) > 0:
    selected_state = state
else:
    selected_state = state_options
locations_data = locations_data[locations_data['STATE'].isin(selected_state)]

# City Selection
city_options = sorted(locations_data['CITY'].unique().tolist())
city = st.sidebar.multiselect('Select a city', city_options, placeholder='All')
if len(city) > 0:
    selected_city = city
    location_options = sorted(locations_data[locations_data['CITY'].isin(selected_city)]['ADDRESS'].unique().tolist())
else:
    selected_city = city_options
    location_options = sorted(locations_data[locations_data['STATE'].isin(selected_state)]['ADDRESS'].unique().tolist())
locations_data = locations_data[locations_data['CITY'].isin(selected_city)]

# Location Selection
location = st.sidebar.multiselect('Select a location', location_options, placeholder='All')
if len(location) > 0:
    selected_location = location
else:
    selected_location = location_options
locations_data = locations_data[locations_data['ADDRESS'].isin(selected_location)]

# Filter reviews based on selected locations
filtered_reviews = reviews_data[reviews_data['PLACE_ID'].isin(locations_data['PLACE_ID'])]

# Sentiment Selection
sentiment_options = sorted(filtered_reviews['OVERALL_SENTIMENT'].unique().tolist())
sentiment = st.sidebar.multiselect('Select a sentiment', sentiment_options, placeholder='All')
if len(sentiment) > 0:
    selected_sentiment = sentiment
else:
    selected_sentiment = sentiment_options
filtered_reviews = filtered_reviews[filtered_reviews['OVERALL_SENTIMENT'].isin(selected_sentiment)]

# Rating Selection
rating_options = sorted(filtered_reviews['RATING'].unique().tolist())
rating = st.sidebar.multiselect('Select a review rating', rating_options, placeholder='All')
if len(rating) > 0:
    selected_rating = rating
else:
    selected_rating = rating_options
filtered_reviews = filtered_reviews[filtered_reviews['RATING'].isin(selected_rating)]

# Date Selection
date_options = ['Last Week', 'Last Month', 'Last 3 Months', 'All Time', 'Other']
date_selection = st.sidebar.selectbox('Select a date', date_options, index=None, placeholder='All')
min_date = pd.to_datetime(filtered_reviews['REVIEW_DATE'].min())
max_date = pd.to_datetime(filtered_reviews['REVIEW_DATE'].max())

if date_selection is None:
    start_date = min_date
    end_date = max_date
elif date_selection == 'Other':
    start_date, end_date = st.sidebar.slider('Select date range', value=[min_date.date(), max_date.date()], min_value=min_date.date(), max_value=max_date.date(), key='date_input')
    start_date = pd.to_datetime(start_date)  # Convert to Timestamp
    end_date = pd.to_datetime(end_date).replace(hour=23, minute=59)  # Convert to Timestamp and set time to 23:59
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

# Convert REVIEW_DATE to datetime for comparison
filtered_reviews['REVIEW_DATE'] = pd.to_datetime(filtered_reviews['REVIEW_DATE'])
filtered_reviews = filtered_reviews[filtered_reviews['REVIEW_DATE'].between(selected_date_range[0], selected_date_range[1])]

filtered_locations_with_reviews = filtered_reviews.merge(locations_data, on='PLACE_ID', how='inner')
sentences_data_filtered = sentences_data[sentences_data['REVIEW_ID'].isin(filtered_locations_with_reviews['REVIEW_ID'])]

if filtered_locations_with_reviews.empty:
    st.info('No data available for the selected filters.', icon=':material/info:')
    st.stop()

st.sidebar.divider()
st.sidebar.caption(f"**Data last updated on:** {data_collected_at}.")

## TABS
if menu_id == 'About':
    introduction()
    
if menu_id == 'Locations':    
    metrics(location_count_total, review_count_total, avg_rating_total, filtered_locations_with_reviews)
    locations(filtered_locations_with_reviews)

if menu_id == 'Overview':
    metrics(location_count_total, review_count_total, avg_rating_total, filtered_locations_with_reviews)
    overview(filtered_locations_with_reviews)

if menu_id == 'AI Analysis':
    metrics(location_count_total, review_count_total, avg_rating_total, filtered_locations_with_reviews, show_pie=True)
    ai_analysis(filtered_locations_with_reviews, attributes, sentences_data_filtered, entities_data)

if menu_id == 'Support':
    support(filtered_locations_with_reviews, reviews_data)

if menu_id == 'Assistant':
    assistant(file_id=st.secrets['FILE_ID'], assistant_id=st.secrets['ASSISTANT_ID'], bot_data=bot_data)