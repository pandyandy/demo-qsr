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


locations_data = pd.read_csv(st.secrets['locations_path'])
reviews_data = read_data(st.secrets['reviews_path'])#pd.read_csv(st.secrets['reviews_path'])
sentences_data = pd.read_csv(st.secrets['sentences_path'])
attributes = pd.read_csv(st.secrets['attributes_path'])
bot_data = pd.read_csv(st.secrets['bot_path'])
reviews_data = reviews_data[reviews_data['REVIEW_ORIGIN'] != 'Facebook']
bot_data = bot_data[bot_data['REVIEW_ORIGIN'] != 'Facebook']


options=['Locations', 'Overview', 'AI Analysis', 'Support', 'Assistant'] #'About',
icons=['pin-map-fill', 'people', 'file-bar-graph', 'chat-heart', 'robot'] #'info-circle', 

menu_id = option_menu(None, options=options, icons=icons, key='menu_id', orientation="horizontal")


# Convert ENTITY and ATTRIBUTE columns to uppercase
sentences_data['ENTITY'] = sentences_data['ENTITY'].str.title()

#attributes['entity'] = attributes['entity'].replace('burgers', 'burger')
pronouns_to_remove = ['i', 'you', 'she', 'he', 'it', 'we', 'they', 'I', 'You', 'She', 'He', 'It', 'We', 'They']
attributes = attributes[~attributes['ENTITY'].isin(pronouns_to_remove)]
#attributes = attributes.groupby(['entity', 'attribute'])['count'].sum().reset_index()#
#attributes = attributes[attributes['count'] > 2]

# Convert REVIEW_DATE to datetime, handling NaT values and potential format issues
reviews_data['REVIEW_DATE'] = pd.to_datetime(reviews_data['REVIEW_DATE'], errors='coerce', format='mixed')
st.sidebar.markdown(
    f'''
        <div style="text-align: center; margin-top: 20px; margin-bottom: 40px;">
            <img src="{LOGO_URL}" alt="Logo" width="200">
        </div>
    ''',
    unsafe_allow_html=True
)
if 'brand_options' not in st.session_state:
    st.session_state.brand_options = sorted(locations_data['CATEGORY_0'].unique().tolist(), reverse=True)

location_count_total = locations_data['PLACE_ID'].nunique()
brand = st.sidebar.multiselect('Select a category', st.session_state.brand_options, placeholder='All', key='selected_brand')

if len(brand) > 0:
    st.session_state.filtered_locations = locations_data[locations_data['CATEGORY_0'].isin(brand)]
else:
    st.session_state.filtered_locations = locations_data

# Merge locations and reviews data for the specific brand and save to session state
if f'locations_reviews_merged_{brand}' not in st.session_state:
    st.session_state[f'locations_reviews_merged_{brand}'] = pd.merge(
        st.session_state.filtered_locations,
        reviews_data,
        on='PLACE_ID',
        how='inner'
    )

if not brand:  # Empty list - show both food and product categories
    categories_to_filter = {
        "Food": {
            "Quality": ["Taste", "Freshness", "Temperature", "Texture", "Appearance/Presentation", "Healthfulness", "Portion"],
            "Menu": ["Comments", "Inquiries"], 
            "Issues": ["Availability", "Food Safety"]
        },
        "Product": {
            "Quality": ["Effectiveness", "Condition", "Reliability", "Appearance", "Features", "Safety", "Quantity"],
            "Selection": ["Availability", "Variety", "Product Information"],
            "Issues": ["Defects", "Expiration", "Packaging Problems"]
        },
        "People": {
            "Team": ["Presentation", "Hospitality", "Professionalism", "Helpfulness", "Friendliness", "Knowledge"]
        },
        "Experience": {
            "Payment": ["Cost of Meal", "Pricing", "Billing Accuracy", "Payment Processing"],
            "Ordering": ["Speed of Service", "Order Accuracy", "Ordering Process", "Ease of Ordering", "Processing Time"],
            "Loyalty": ["Loyalty", "Loyalty Program", "Return Incentives"],
            "Facilities": ["Amenities", "Cleanliness", "Accessibility", "Waiting Area", "Parking"],
            "Events": ["Weddings", "Receptions", "Private Events"],
            "Inquiries": ["Inquiries", "Responsiveness", "Staff Communication"],
            "Cleanliness": ["Dining Room", "Kitchen", "Bathrooms", "Patio", "Drive-in", "Garbage"],
            "General Feedback": ["Overall Impression", "Unspecified"]
        }
    }
    restaurant_tf = True

elif 'Restaurant' in brand and len(brand) == 1:  # Only restaurant category
    categories_to_filter = {
        "Food": {
            "Quality": ["Taste", "Freshness", "Temperature", "Texture", "Appearance/Presentation", "Healthfulness", "Portion"],
            "Menu": ["Comments", "Inquiries"],
            "Issues": ["Availability", "Food Safety"]
        },
        "People": {
            "Team": ["Presentation", "Hospitality"]
        },
        "Experience": {
            "Payment": ["Cost of Meal", "Pricing Accuracy", "Payment Processing"],
            "Ordering": ["Speed of Service", "Order Accuracy", "Ordering Process"],
            "Loyalty": ["Loyalty"],
            "Amenities": ["Amenities"],
            "Inquiries": ["Inquiries"],
            "Cleanliness": ["Dining Room", "Kitchen", "Bathrooms", "Patio", "Drive-in", "Garbage"]
        }
    }
    restaurant_tf = True

elif 'Restaurant' not in brand:  # Only product categories
    categories_to_filter = {
        "Product": {
            "Quality": ["Effectiveness", "Condition", "Reliability", "Appearance", "Features", "Safety", "Quantity"],
            "Selection": ["Availability", "Variety", "Product Information"],
            "Issues": ["Defects", "Expiration", "Packaging Problems"]
        },
        "People": {
            "Team": ["Professionalism", "Helpfulness", "Friendliness", "Knowledge"]
        },
        "Experience": {
            "Payment": ["Pricing", "Billing Accuracy", "Payment Processing"],
            "Ordering": ["Ease of Ordering", "Processing Time", "Order Accuracy"],
            "Loyalty": ["Loyalty Program", "Return Incentives"],
            "Facilities": ["Cleanliness", "Accessibility", "Waiting Area", "Parking"],
            "Events": ["Weddings", "Receptions", "Private Events"],
            "Inquiries": ["Responsiveness", "Staff Communication"],
            "General Feedback": ["Overall Impression", "Unspecified"]
        }
    }
    restaurant_tf = False

else:  # Restaurant and other categories
    categories_to_filter = {
        "Food": {
            "Quality": ["Taste", "Freshness", "Temperature", "Texture", "Appearance/Presentation", "Healthfulness", "Portion"],
            "Menu": ["Comments", "Inquiries"],
            "Issues": ["Availability", "Food Safety"]
        },
        "Product": {
            "Quality": ["Effectiveness", "Condition", "Reliability", "Appearance", "Features", "Safety", "Quantity"],
            "Selection": ["Availability", "Variety", "Product Information"],
            "Issues": ["Defects", "Expiration", "Packaging Problems"]
        },
        "People": {
            "Team": ["Presentation", "Hospitality", "Professionalism", "Helpfulness", "Friendliness", "Knowledge"]
        },
        "Experience": {
            "Payment": ["Cost of Meal", "Pricing", "Billing Accuracy", "Payment Processing"],
            "Ordering": ["Speed of Service", "Order Accuracy", "Ordering Process", "Ease of Ordering", "Processing Time"],
            "Loyalty": ["Loyalty", "Loyalty Program", "Return Incentives"],
            "Facilities": ["Amenities", "Cleanliness", "Accessibility", "Waiting Area", "Parking"],
            "Events": ["Weddings", "Receptions", "Private Events"],
            "Inquiries": ["Inquiries", "Responsiveness", "Staff Communication"],
            "Cleanliness": ["Dining Room", "Kitchen", "Bathrooms", "Patio", "Drive-in", "Garbage"],
            "General Feedback": ["Overall Impression", "Unspecified"]
        }
    }
    restaurant_tf = True

# Calculate the correct location count by counting unique PLACE_IDs
#location_count_total = st.session_state.filtered_locations['PLACE_ID'].nunique()
data_collected_at = st.session_state.filtered_locations['DATA_COLLECTED_AT'].max()

# Calculate review count and average rating based on selected brand
review_count_total = len(st.session_state[f'locations_reviews_merged_{brand}'])
avg_rating_total = round(st.session_state[f'locations_reviews_merged_{brand}']['RATING'].mean(), 2)

# Brand Selection
brand_options = sorted(st.session_state[f'locations_reviews_merged_{brand}']['BRAND'].unique().tolist())
brand_select = st.sidebar.multiselect('Select a brand', brand_options, placeholder='All')
if len(brand_select) > 0:
    selected_brand = brand_select
else:
    selected_brand = brand_options

# Location Selection
location_options = sorted(st.session_state[f'locations_reviews_merged_{brand}']['ADDRESS'].unique().tolist())
location = st.sidebar.multiselect('Select a location', location_options, placeholder='All')
if len(location) > 0:
    selected_location = location
else:
    selected_location = location_options

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
date_options = ['2024+', 'Current Year', 'Last Year', 'All Time Collected', 'Other']
date_selection = st.sidebar.selectbox('Select a date', date_options, index=0, placeholder='All')
min_date = pd.to_datetime(st.session_state[f'locations_reviews_merged_{brand}']['REVIEW_DATE'].min())
max_date = pd.to_datetime(st.session_state[f'locations_reviews_merged_{brand}']['REVIEW_DATE'].max())

if date_selection == 'Other':
    if min_date == max_date:  # Check if min and max dates are the same
        start_date = min_date
        end_date = max_date.replace(hour=23, minute=59)
    else:
        start_date, end_date = st.sidebar.slider(
            'Select date range',
            value=[min_date.date(), max_date.date()],
            min_value=min_date.date(),
            max_value=max_date.date(),
            key='date_input'
        )
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date).replace(hour=23, minute=59)
else:
    end_date = pd.to_datetime('today')
    if date_selection == 'Current Year':
        start_date = pd.to_datetime(f"{end_date.year}-01-01")
    elif date_selection == 'Last Year':
        start_date = end_date - pd.DateOffset(years=1)
    elif date_selection == 'All Time Collected':
        start_date = min_date
    elif date_selection == '2024+':
        start_date = pd.to_datetime('2024-01-01')

if start_date > end_date:
    start_date, end_date = end_date, start_date

selected_date_range = (start_date, end_date)

filtered_data = st.session_state[f'locations_reviews_merged_{brand}'][
    st.session_state[f'locations_reviews_merged_{brand}']['BRAND'].isin(selected_brand)
]
filtered_data = filtered_data[
    filtered_data['ADDRESS'].isin(selected_location)
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

filtered_data = filtered_data[
    filtered_data['REVIEW_DATE'].between(selected_date_range[0].strftime('%Y-%m-%d %H:%M'), selected_date_range[1].strftime('%Y-%m-%d %H:%M'))
]   

# Order by REVIEW_DATE
filtered_data = filtered_data.sort_values(by='REVIEW_DATE', ascending=False)
sentences_data = sentences_data[sentences_data['REVIEW_ID'].isin(filtered_data['REVIEW_ID'])]

if filtered_data.empty:
    st.info('No data available for the selected filters.', icon=':material/info:')
    st.stop()

st.sidebar.divider()
st.sidebar.caption(f"**Data last updated on:** {data_collected_at}.")

## TABS
#if menu_id == 'About':
#    introduction()
    
if menu_id == 'Locations':    
    metrics(location_count_total, review_count_total, avg_rating_total, filtered_data)
    locations(filtered_data)

if menu_id == 'Overview':
    metrics(location_count_total, review_count_total, avg_rating_total, filtered_data)
    overview(filtered_data)

if menu_id == 'AI Analysis':
    metrics(location_count_total, review_count_total, avg_rating_total, filtered_data, show_pie=True)
    ai_analysis(filtered_data, attributes, sentences_data, categories_to_filter, restaurant_tf)

if menu_id == 'Support':
    support(filtered_data, reviews_data)

if menu_id == 'Assistant':
    assistant(file_id=st.secrets['FILE_ID'], assistant_id=st.secrets['ASSISTANT_ID'], bot_data=bot_data)