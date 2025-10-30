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

    center_lat = state_coords['LATITUDE']
    center_long = state_coords['LONGITUDE']

    # Convert color arrays to hex for HTML
    def color_to_hex(color_array):
        return f"#{color_array[0]:02x}{color_array[1]:02x}{color_array[2]:02x}"
    
    map_data['hex_color'] = map_data['RATING'].apply(lambda x: color_to_hex(get_color(x)))
    # Scale icon size based on review count for visual distinction
    map_data['icon_size'] = map_data['COUNT'].apply(lambda x: min(max(x * 5, 25), 50))
    
    # Create HTML-based icons with colored backgrounds
    def create_icon_data(row):
        size = int(row['icon_size'])
        color = row['hex_color']
        html = f'''
            <div style="color: white; background-color: {color}; width: {size}px; height: {size}px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                <span style="font-size: {size//2}px;">📍</span>
            </div>
        '''
        return {
            "url": f"data:image/svg+xml;charset=utf-8,{html.replace('#', '%23').replace('<', '%3C').replace('>', '%3E').replace(' ', '%20').replace('"', '%22').replace("'", '%27')}",
            "width": size,
            "height": size,
            "anchorY": size,
        }
    
    map_data['icon_data'] = map_data.apply(create_icon_data, axis=1)
    
    icon_layer = pdk.Layer(
        "IconLayer",
        data=map_data,
        get_position=["LONGITUDE", "LATITUDE"],
        get_icon="icon_data",
        size_scale=1,
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_long,
        zoom=8,
        pitch=0
    )

    deck = pdk.Deck(
        initial_view_state=view_state,
        map_style=None,
        layers=[icon_layer],
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
    st.caption("_The size of the pin represents the number of collected reviews, the color represents the average rating._")
