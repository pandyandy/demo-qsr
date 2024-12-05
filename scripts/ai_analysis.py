import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import plotly.express as px

from scripts.viz import sentiment_color

def create_network_graph(attributes, slider_entities):
    # Get top entities by total attribute counts
    pivot_attrs = attributes.pivot(index='entity', columns='attribute', values='count').fillna(0)
    pivot_attrs['Total'] = pivot_attrs.sum(axis=1)
    top_entities = pivot_attrs.nlargest(slider_entities, 'Total').index.tolist()
    
    # Initialize graph and figure
    G = nx.Graph()
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Calculate entity positions in a circle
    entity_positions = calculate_entity_positions(top_entities)
    
    # Add nodes and edges to graph
    add_nodes_and_edges(G, top_entities, attributes)
    
    # Position attribute nodes
    pos = position_attribute_nodes(G, entity_positions)
    
    # Draw the network
    draw_network(G, pos, top_entities)
    
    # Configure plot
    ax.axis('off')
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    
    return fig

def calculate_entity_positions(entities, radius=1.5):
    return {entity: (radius * np.cos(2 * np.pi * i / len(entities)), radius * np.sin(2 * np.pi * i / len(entities))) 
            for i, entity in enumerate(entities)}

def add_nodes_and_edges(G, top_entities, attributes):
    for entity in top_entities:
        G.add_node(entity, node_type='entity')
        entity_attrs = attributes[attributes['entity'] == entity]
        
        for _, row in entity_attrs.iterrows():
            attr, count = row['attribute'], row['count']
            G.add_node(attr, node_type='attribute') if attr not in G else None
            G.add_edge(entity, attr, weight=count)

def position_attribute_nodes(G, entity_positions, scale_factor=0.8):
    pos = entity_positions.copy()
    attr_nodes = [n for n in G.nodes() if n not in entity_positions]
    attr_connections = {attr: len([n for n in G.neighbors(attr) if n in entity_positions]) for attr in attr_nodes}
    attr_nodes.sort(key=lambda x: attr_connections[x], reverse=True)
    
    occupied_positions = []
    min_distance = 0.2

    for attr in attr_nodes:
        connected_entities = [n for n in G.neighbors(attr) if n in entity_positions]
        if connected_entities:
            attempts = 0
            while attempts < 50:
                if attr_connections[attr] > 1:
                    x, y = np.mean([entity_positions[e] for e in connected_entities], axis=0) * scale_factor
                    offset = 0.15 + (0.1 * attempts / 50)
                    angle = np.random.uniform(0, 2 * np.pi)
                    x += offset * np.cos(angle)
                    y += offset * np.sin(angle)
                else:
                    entity = connected_entities[0]
                    angle = 2 * np.pi * attempts / 50
                    radius = 0.25 + (0.1 * attempts / 50)
                    x = entity_positions[entity][0] + radius * np.cos(angle)
                    y = entity_positions[entity][1] + radius * np.sin(angle)

                position = (x, y)
                if all(np.sqrt((x - ox)**2 + (y - oy)**2) > min_distance for ox, oy in occupied_positions):
                    occupied_positions.append(position)
                    pos[attr] = position
                    break
                
                attempts += 1
            
            if attr not in pos:
                pos[attr] = position
                occupied_positions.append(position)

    return pos

def draw_network(G, pos, top_entities):
    attr_nodes = [n for n in G.nodes() if n not in top_entities]
    nx.draw_networkx_nodes(G, pos, nodelist=top_entities, node_color='#e6f2ff', node_size=2500)
    nx.draw_networkx_nodes(G, pos, nodelist=attr_nodes, node_color='#F2F2F2', node_size=1000, alpha=0.7)
    
    colors = plt.cm.rainbow(np.linspace(0, 1, len(top_entities)))
    for i, entity in enumerate(top_entities):
        entity_edges = [(u, v) for (u, v) in G.edges() if u == entity or v == entity]
        if entity_edges:
            edge_weights = [G[u][v]['weight'] for u, v in entity_edges]
            nx.draw_networkx_edges(G, pos, edgelist=entity_edges, 
                                     width=[w / max(edge_weights) * 2 for w in edge_weights],
                                     edge_color=[colors[i]], alpha=0.7)
    
    nx.draw_networkx_labels(G, pos, labels={node: node for node in top_entities}, font_size=10, font_color='#238dff', font_weight='600')
    nx.draw_networkx_labels(G, pos, labels={node: node for node in attr_nodes}, font_size=8)

@st.fragment
def display_network_graph(attributes):
    st.markdown("##### Entity-Attribute Relations")
    st.caption("_See up to top 15 mentioned entities and their attributes._")
    col1, col2 = st.columns([0.9, 0.1], vertical_alignment='center')
    num_entities = col2.number_input("Select the number of entities", min_value=1, max_value=15, value=5)
    fig = create_network_graph(attributes, num_entities)
    col1.pyplot(fig, use_container_width=True)


def ai_analysis(data, attributes, sentences):
    ## SENTIMENT COUNT BY DATE
    data['REVIEW_DATE'] = pd.to_datetime(data['REVIEW_DATE']).dt.date
    avg_rating_per_day = data.groupby('REVIEW_DATE')['RATING'].mean().reset_index()
    color_scale = avg_rating_per_day['RATING'].apply(lambda x: '#EA4335' if x < 1.5 else '#e98f41' if x < 2.5 else '#FBBC05' if x < 3.6 else '#a5c553' if x < 4.5 else '#34A853').tolist()

    fig_avg_rating_per_day = px.line(
        avg_rating_per_day,
        x='REVIEW_DATE',
        y='RATING',
        labels={'RATING': 'Average Rating', 'REVIEW_DATE': 'Date'},
        title='Average Rating by Date',
        height=300
    )
    fig_avg_rating_per_day.update_traces(mode='lines+markers', hovertemplate='Avg Rating: %{y:.2f}<extra></extra>', line=dict(color='#E6E6E6'), marker=dict(color=color_scale))  
    fig_avg_rating_per_day.update_layout(xaxis_title=None, yaxis_title=None, hovermode='x')
    st.plotly_chart(fig_avg_rating_per_day, use_container_width=True)

    ## AVERAGE DETAILED RATING BY DATE
    avg_detailed_rating_by_date = (
        data.groupby('REVIEW_DATE')[['REVIEW_DETAILED_FOOD', 'REVIEW_DETAILED_SERVICE', 'REVIEW_DETAILED_ATMOSPHERE']]
        .mean()
        .round(2)
        .rename(columns={
            'REVIEW_DETAILED_FOOD': 'Food',
            'REVIEW_DETAILED_SERVICE': 'Service', 
            'REVIEW_DETAILED_ATMOSPHERE': 'Atmosphere'
        })
    )
    fig_avg_detailed_rating_by_date = px.line(
        avg_detailed_rating_by_date,
        x=avg_detailed_rating_by_date.index,
        y=['Food', 'Service', 'Atmosphere'],
        labels={'x': 'Date', 'value': 'Avg Score', 'variable': 'Avg Rating', 'REVIEW_DATE': 'Date'},
        title='Average Detailed Rating by Date',
        height=300 
    )

    blue_shades = ['#57aeff', '#0a89ff', '#bddfff']
    for i, trace in enumerate(fig_avg_detailed_rating_by_date.data):
        trace.line.color = blue_shades[i]

    fig_avg_detailed_rating_by_date.update_traces(mode='lines+markers', hovertemplate='Avg Rating: %{y:.2f}<extra></extra>')
    fig_avg_detailed_rating_by_date.update_layout(xaxis_title=None, yaxis_title=None, hovermode='x')
    st.plotly_chart(fig_avg_detailed_rating_by_date)
    
    ## ENTITY-ATTRIBUTE RELATIONS
    st.divider()
    display_network_graph(attributes)

    ## ENTITY CLASSIFICATION
    @st.fragment
    def entity_classification(data, sentences):
        col1, col2, col3 = st.columns([0.3, 0.35, 0.35], gap='medium', vertical_alignment='center')
        with col1:
            st.markdown("##### Classification")
            entities_x = col1.slider("Select the number of entities", min_value=1, max_value=20, value=10)

            categories = {
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

            category_options = list(categories.keys())
            #category_options = sorted(sentences[sentences['CATEGORY'] != 'Unknown']['CATEGORY'].unique().tolist())
            category = st.multiselect("Select categories", options=category_options, placeholder='All')
            if len(category) > 0:
                selected_category = category
            else:
                selected_category = category_options

            filtered_sentences = sentences[sentences['CATEGORY'].isin(selected_category)]

            groups = []
            for cat in selected_category:
                groups.extend(categories[cat].keys())
            group_options = list(set(groups))
            
            #group_options = sorted(filtered_sentences[filtered_sentences['CATEGORY_GROUP'] != 'Unknown']['CATEGORY_GROUP'].unique().tolist())
            group = st.multiselect("Select groups", options=group_options, placeholder='All')
            if len(group) > 0:
                selected_group = group
                topics = []
                for g in selected_group:
                    for cat in selected_category:
                        if g in categories[cat]:
                            topics.extend(categories[cat][g])
                topic_options = list(set(topics))
            else:
                selected_group = group_options
                topics = []
                for g in selected_group:
                    for cat in selected_category:
                        if g in categories[cat]:
                            topics.extend(categories[cat][g])
                topic_options = list(set(topics))

            filtered_sentences = filtered_sentences[filtered_sentences['CATEGORY_GROUP'].isin(selected_group)]
            
            #topic_options = sorted(filtered_sentences[filtered_sentences['TOPIC'] != 'Unknown']['TOPIC'].unique().tolist())
            topic = st.multiselect("Select topics", options=topic_options, placeholder='All')        
            if len(topic) > 0:
                selected_topic = topic
            else:
                selected_topic = topic_options
            filtered_sentences = filtered_sentences[filtered_sentences['TOPIC'].isin(selected_topic)]

        with col2:
            filtered_entities = filtered_sentences[filtered_sentences['SENTENCE_SENTIMENT'] == 'Positive']
            positive_entities = filtered_entities['ENTITY'].value_counts().head(entities_x).sort_values(ascending=True)
            if not positive_entities.empty:
                fig_positive = px.bar(
                    positive_entities,
                    x=positive_entities.values,
                    y=positive_entities.index,
                    orientation='h',
                    title='Positive Entities',
                    text=positive_entities.values
                )
                fig_positive.update_layout(
                    xaxis_title=None,
                    yaxis_title=None,
                    hovermode=False
                )
                fig_positive.update_traces(
                    marker_color='#34A853',
                    textposition='inside'
                )
                st.plotly_chart(fig_positive)
            else:
                st.info("No positive entities found for the selected filters.", icon=':material/info:')
                
        with col3:
            filtered_entities = filtered_sentences[filtered_sentences['SENTENCE_SENTIMENT'] == 'Negative']
            negative_entities = filtered_entities['ENTITY'].value_counts().head(entities_x).sort_values(ascending=True)
            if not negative_entities.empty:
                fig_negative = px.bar(
                    negative_entities,
                    x=negative_entities.values,
                    y=negative_entities.index,
                    orientation='h',
                    title='Negative Entities',
                    text=negative_entities.values
                )
                fig_negative.update_layout(
                    xaxis_title=None,
                    yaxis_title=None,
                    hovermode=False
                )
                fig_negative.update_traces(
                    marker_color='#EA4335',
                    textfont_color='white',
                    textposition='inside'
                )
                st.plotly_chart(fig_negative)
            else:
                st.info("No negative entities found for the selected filters.", icon=':material/info:')

        ## REVIEW DETAILS
        st.markdown("##### Review Details")
        # Filter data based on selected filters
        unique_review_ids = filtered_sentences['REVIEW_ID'].unique()
        filtered_review_data = data[data['REVIEW_ID'].isin(unique_review_ids)].sort_values('REVIEW_DATE', ascending=False)
        
        if filtered_review_data.empty:
            st.info("No reviews with feedback text available for the selected filters.", icon=':material/info:')
            st.stop()

        columns = ['REVIEW_DATE', 'RATING', 'REVIEW_TEXT', 'OVERALL_SENTIMENT', 'ADDRESS', 'CATEGORY', 'CATEGORY_GROUP', 'TOPIC', 'ENTITY', 'REVIEWER_NAME', 'REVIEW_URL']
        st.dataframe(filtered_review_data[columns],
                     #.style.map(sentiment_color, subset=["OVERALL_SENTIMENT"]),
                    column_config={
                        'REVIEW_DATE': 'Date',
                        'RATING': 'Rating',
                        'REVIEW_TEXT': st.column_config.Column(
                            'Review',
                            width="large"),
                        'OVERALL_SENTIMENT': 'Sentiment',
                        'ADDRESS': st.column_config.Column(
                            'Location',
                            width="small"),
                        'CATEGORY': st.column_config.Column(
                            'Category',
                            width="medium"),
                        'CATEGORY_GROUP': st.column_config.Column(
                            'Group',
                            width="medium"),
                        'TOPIC': st.column_config.Column(
                            'Topic',
                            width="medium"),
                        'ENTITY': st.column_config.Column(
                            'Entities',
                            width="medium"),
                        'REVIEWER_NAME': 'Author',
                        'REVIEW_URL': st.column_config.LinkColumn(
                            '🔗',
                            width='small',
                            help='Link to the review',
                            display_text='URL')
                    },
                    column_order=columns,
                    hide_index=True, 
                    use_container_width=True)
    

    data = data[data['REVIEW_TEXT'].notna()]
    data = data.merge(
        sentences.groupby('REVIEW_ID').agg(
            ENTITY=('ENTITY', lambda x: [entity for entity in x if entity and pd.notna(entity)]),
            CATEGORY=('CATEGORY', lambda x: [cat for cat in x.unique().tolist() if cat != 'Unknown']),
            CATEGORY_GROUP=('CATEGORY_GROUP', lambda x: [group for group in x.unique().tolist() if group != 'Unknown']),
            TOPIC=('TOPIC', lambda x: [topic for topic in x.unique().tolist() if topic != 'Unknown'])
        ).reset_index(),
        on='REVIEW_ID',
        how='left'
    )

    entity_classification(data, sentences)