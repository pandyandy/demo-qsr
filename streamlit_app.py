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

# Initialize session state variables
session_defaults = {
    "thread_id": None,
    "messages": [{'role': 'assistant', 'content': 'Welcome! How can I assist you today?'}],
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
sentences_data = pd.read_csv(st.secrets['sentences_path'])
attributes = pd.read_csv(st.secrets['attributes_path'])
#bot_data = pd.read_csv(st.secrets['bot_path'])

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

if 'brand_options' not in st.session_state:
    st.session_state.brand_options = locations_data['BRAND'].unique().tolist()

brand = st.sidebar.selectbox('Select a brand', st.session_state.brand_options, index=0, placeholder='All', key='selected_brand') if st.secrets.get('all_brands', 'True') == 'True' else st.secrets['brand_filter']
st.session_state.filtered_locations = locations_data[locations_data['BRAND'] == brand]

# Merge locations and reviews data for the specific brand and save to session state
if f'locations_reviews_merged_{brand}' not in st.session_state:
    st.session_state[f'locations_reviews_merged_{brand}'] = pd.merge(
        st.session_state.filtered_locations,
        reviews_data,
        on='PLACE_ID',
        how='inner'
    )

location_count_total = len(st.session_state.filtered_locations)
data_collected_at = st.session_state.filtered_locations['DATA_COLLECTED_AT'].max()

# Calculate review count and average rating based on selected brand
review_count_total = len(st.session_state[f'locations_reviews_merged_{brand}'])
#avg_rating_total = st.session_state.locations_reviews_merged['RATING'].mean().round(2)
avg_rating_total = round(st.session_state[f'locations_reviews_merged_{brand}']['RATING'].mean(), 2)
# State Selection
state_options = sorted(st.session_state.filtered_locations['STATE'].unique().tolist())
state = st.sidebar.multiselect('Select a state', state_options, placeholder='All')
if len(state) > 0:
    selected_state = state
else:
    selected_state = state_options

# City Selection
#city_options = sorted(locations_reviews_merged['CITY'].unique().tolist())
city_options = sorted(st.session_state.filtered_locations[st.session_state.filtered_locations['STATE'].isin(selected_state)]['CITY'].unique().tolist())
city = st.sidebar.multiselect('Select a city', city_options, placeholder='All')
if len(city) > 0:
    selected_city = city
    location_options = sorted(st.session_state.filtered_locations[st.session_state.filtered_locations['CITY'].isin(selected_city)]['ADDRESS'].unique().tolist())
else:
    selected_city = city_options
    location_options = sorted(st.session_state.filtered_locations[st.session_state.filtered_locations['STATE'].isin(selected_state)]['ADDRESS'].unique().tolist())

# Location Selection
location = st.sidebar.multiselect('Select a location', location_options, placeholder='All')
if len(location) > 0:
    selected_location = location
else:
    selected_location = location_options

# Filter reviews based on selected locations
#filtered_reviews = reviews_data[reviews_data['PLACE_ID'].isin(locations_data['PLACE_ID'])]

# Sentiment Selection
sentiment_options = sorted(st.session_state[f'locations_reviews_merged_{brand}']['OVERALL_SENTIMENT'].unique().tolist())
sentiment = st.sidebar.multiselect('Select a sentiment', sentiment_options, placeholder='All')
if len(sentiment) > 0:
    selected_sentiment = sentiment
else:
    selected_sentiment = sentiment_options

# Rating Selection
rating_options = sorted(st.session_state[f'locations_reviews_merged_{brand}']['RATING'].unique().tolist())
rating = st.sidebar.multiselect('Select a review rating', rating_options, placeholder='All')
if len(rating) > 0:
    selected_rating = rating
else:
    selected_rating = rating_options

# Date Selection
date_options = ['Last Week', 'Last Month', 'Last 3 Months', 'All Time', 'Other']
date_selection = st.sidebar.selectbox('Select a date', date_options, index=None, placeholder='All')
min_date = pd.to_datetime(st.session_state[f'locations_reviews_merged_{brand}']['REVIEW_DATE'].min())
max_date = pd.to_datetime(st.session_state[f'locations_reviews_merged_{brand}']['REVIEW_DATE'].max())

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

filtered_data = st.session_state[f'locations_reviews_merged_{brand}'][
    st.session_state[f'locations_reviews_merged_{brand}']['STATE'].isin(selected_state)
]
filtered_data = filtered_data[
    filtered_data['CITY'].isin(selected_city)
]
filtered_data = filtered_data[
    filtered_data['ADDRESS'].isin(selected_location)
]
filtered_data = filtered_data[
    filtered_data['OVERALL_SENTIMENT'].isin(selected_sentiment)
]
filtered_data = filtered_data[
    filtered_data['RATING'].isin(selected_rating)
]

# Convert REVIEW_DATE to datetime for comparison
filtered_data['REVIEW_DATE'] = pd.to_datetime(filtered_data['REVIEW_DATE']).dt.strftime('%Y-%m-%d %H:%M')
filtered_data = filtered_data[
    filtered_data['REVIEW_DATE'].between(selected_date_range[0].strftime('%Y-%m-%d %H:%M'), selected_date_range[1].strftime('%Y-%m-%d %H:%M'))
]   

# Order by REVIEW_DATE
filtered_data = filtered_data.sort_values(by='REVIEW_DATE', ascending=False)


if filtered_data.empty:
    st.info('No data available for the selected filters.', icon=':material/info:')
    st.stop()

st.sidebar.divider()
st.sidebar.caption(f"**Data last updated on:** {data_collected_at}.")

## TABS
if menu_id == 'About':
    introduction()
    
if menu_id == 'Locations':    
    metrics(location_count_total, review_count_total, avg_rating_total, filtered_data)
    locations(filtered_data)

if menu_id == 'Overview':
    metrics(location_count_total, review_count_total, avg_rating_total, filtered_data)
    overview(filtered_data)

if menu_id == 'AI Analysis':
    metrics(location_count_total, review_count_total, avg_rating_total, filtered_data, show_pie=True)
    ai_analysis(filtered_data, attributes, sentences_data)

if menu_id == 'Support':
    support(filtered_data, reviews_data)

if menu_id == 'Assistant':
    assistant(file_id=st.secrets['FILE_ID'], assistant_id=st.secrets['ASSISTANT_ID']) #, bot_data=bot_data)