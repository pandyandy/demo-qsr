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
    map_data = data.groupby(['ADDRESS', 'LATITUDE', 'LONGITUDE', 'BRAND', 'PLACE_TOTAL_SCORE']).agg({
        'REVIEW_ID': 'count',
        'RATING': 'mean'
    }).reset_index().rename(columns={'REVIEW_ID': 'COUNT'})
    if map_data.empty:
        st.info("No map data available.", icon=':material/info:')
        st.stop()
    map_data['RATING'] = map_data['RATING'].round(2)
    
    # Calculate center coordinates from all data points
    center_coords = map_data.agg({
        'LATITUDE': 'mean',
        'LONGITUDE': 'mean'
    })

    center_lat = center_coords['LATITUDE']
    center_long = center_coords['LONGITUDE']

    map_data['color'] = map_data['RATING'].apply(get_color)
    
    # Normalize heights if you want a fixed maximum height
    max_count = map_data['COUNT'].max()
    map_data['normalized_count'] = map_data['COUNT'] / max_count * 100  # Scale to 0-100 range

    column_layer = pdk.Layer(
        "ColumnLayer",
        data=map_data,
        disk_resolution=12,
        radius=50,
        elevation_scale=20,
        get_position=["LONGITUDE", "LATITUDE"],
        get_color="color",
        get_elevation="normalized_count",  # Use normalized count instead of raw count
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_long,
        zoom=12,
        pitch=50
    )

    deck = pdk.Deck(
        initial_view_state=view_state,
        map_style=None,
        layers=[column_layer],
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
    st.caption("_The height of the column represents the number of collected reviews, the color represents the average rating._")
