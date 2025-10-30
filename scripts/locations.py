import streamlit as st
import pandas as pd
import pydeck as pdk

def get_color(rating):
    if rating <= 1:
        return [234, 67, 53, 255]
    elif rating <= 2:
        return [233, 143, 65, 255]
    elif rating <= 3:
        return [251, 189, 5, 255]
    elif rating <= 4:
        return [165, 197, 83, 255]
    else:
        return [52, 168, 83, 255]

def locations(data):
    map_data = data.groupby(['ADDRESS', 'LATITUDE', 'LONGITUDE', 'STATE', 'BRAND', 'PLACE_TOTAL_SCORE']).agg({
        'REVIEW_ID': 'count',
        'RATING': 'mean'
    }).reset_index().rename(columns={'REVIEW_ID': 'COUNT'})
    if map_data.empty:
        st.info("No map data available.", icon=':material/info:')
        st.stop()
    map_data['RATING'] = map_data['RATING'].round(2)
    state_reviews = map_data.groupby('STATE')['COUNT'].sum().reset_index()
    state_reviews = state_reviews.sort_values('COUNT', ascending=False)
    state_with_most_reviews = state_reviews.iloc[0]['STATE']
    state_coords = map_data[map_data['STATE'] == state_with_most_reviews].agg({
        'LATITUDE': 'mean',
        'LONGITUDE': 'mean'
    })

    # Set center to Canada's geographic center for country-wide view
    center_lat = 56.1304  # Canada's approximate center latitude
    center_long = -106.3468  # Canada's approximate center longitude

    map_data['color'] = map_data['RATING'].apply(get_color)
    # Scale radius based on review count for visual distinction - smaller dots for Canada-wide view
    map_data['radius'] = map_data['COUNT'].apply(lambda x: min(max(x * 2, 8), 20))
    
    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position=["LONGITUDE", "LATITUDE"],
        get_color="color",
        get_radius="radius",
        pickable=True,
        stroked=True,
        filled=True,
        get_line_color=[255, 255, 255, 200],
        get_line_width=2
    )

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_long,
        zoom=3.5,  # Zoomed out to show all of Canada
        pitch=0
    )

    deck = pdk.Deck(
        initial_view_state=view_state,
        map_style=None,
        layers=[scatterplot_layer],
        tooltip={
            "text": "Brand: {BRAND}\nLocation: {ADDRESS}\nLocation Rating: {PLACE_TOTAL_SCORE}\nCollected Reviews: {COUNT}\nAvg Review Rating: {RATING}",
            "style": {
                "backgroundColor": "white",
                "color": "black",
                "fontSize": "16px"
            }
        }
    )
    st.pydeck_chart(deck, use_container_width=True, height=700)
    st.caption("_The size of the dot represents the number of collected reviews, the color represents the average rating._")
