import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

def predictive_alerts(data):
    st.header("🚨 Predictive Alerts & Early Warning System")
    st.markdown("Identifying locations at risk of declining performance using advanced analytics")

    if 'REVIEW_DATE' not in data.columns or 'RATING' not in data.columns:
        st.warning("Not enough data to show predictive alerts.")
        return

    # Ensure date is datetime
    data['REVIEW_DATE'] = pd.to_datetime(data['REVIEW_DATE'])
    
    # Create tabs for different alert types
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Location Alerts", "📊 Trend Analysis", "🔍 Risk Factors", "📈 Performance Forecast"])
    
    with tab1:
        st.subheader("At-Risk Locations Detection")
        
        # Group by location and calculate metrics
        location_metrics = calculate_location_risk_metrics(data)
        
        if location_metrics.empty:
            st.info("No location data available for analysis.")
            return
        
        # Identify at-risk locations
        at_risk_locations = identify_at_risk_locations(location_metrics)
        
        if at_risk_locations:
            st.warning(f"⚠️ **{len(at_risk_locations)} locations identified as at-risk!**")
            
            # Display at-risk locations table
            risk_df = pd.DataFrame(at_risk_locations)
            st.dataframe(risk_df, use_container_width=True)
            
            # Show detailed analysis for top at-risk location
            if len(at_risk_locations) > 0:
                top_risk = at_risk_locations[0]
                st.subheader(f"🔍 Detailed Analysis: {top_risk['Location']}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Risk Score", f"{top_risk['Risk Score']:.1f}")
                with col2:
                    st.metric("Rating Trend", f"{top_risk['Rating Trend']:.2f}")
                with col3:
                    st.metric("Sentiment Trend", f"{top_risk['Sentiment Trend']:.3f}")
                with col4:
                    st.metric("Complaint Rate", f"{top_risk['Complaint Rate']:.1%}")
                
                # Show risk factors
                st.write("**Risk Factors:**")
                for factor in top_risk['Risk Factors'].split('; '):
                    st.write(f"• {factor}")
        else:
            st.success("✅ No at-risk locations detected!")
    
    with tab2:
        st.subheader("Trend Analysis & Rolling Averages")
        
        # Location selector for trend analysis
        location_options = sorted(data['ADDRESS'].unique())
        selected_location = st.selectbox("Select a location for trend analysis", location_options)
        
        if selected_location:
            location_data = data[data['ADDRESS'] == selected_location].sort_values('REVIEW_DATE')
            
            if len(location_data) >= 3:
                # Calculate rolling averages
                location_data['rolling_rating'] = location_data['RATING'].rolling(window=7, min_periods=1).mean()
                location_data['rolling_sentiment'] = location_data['OVERALL_SENTIMENT'].rolling(window=7, min_periods=1).mean()
                
                # Create trend chart
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('Rating Trends', 'Sentiment Trends'),
                    vertical_spacing=0.1
                )
                
                # Rating trend
                fig.add_trace(
                    go.Scatter(x=location_data['REVIEW_DATE'], y=location_data['RATING'], 
                              mode='markers', name='Individual Ratings', marker=dict(size=4)),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(x=location_data['REVIEW_DATE'], y=location_data['rolling_rating'], 
                              mode='lines', name='7-Day Rolling Average', line=dict(width=3)),
                    row=1, col=1
                )
                
                # Sentiment trend
                fig.add_trace(
                    go.Scatter(x=location_data['REVIEW_DATE'], y=location_data['OVERALL_SENTIMENT'], 
                              mode='markers', name='Individual Sentiment', marker=dict(size=4)),
                    row=2, col=1
                )
                fig.add_trace(
                    go.Scatter(x=location_data['REVIEW_DATE'], y=location_data['rolling_sentiment'], 
                              mode='lines', name='7-Day Rolling Average', line=dict(width=3)),
                    row=2, col=1
                )
                
                fig.update_layout(height=600, title_text=f"Trend Analysis for {selected_location}")
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate trend statistics
                recent_rating = location_data['RATING'].tail(10).mean()
                recent_sentiment = location_data['OVERALL_SENTIMENT'].tail(10).mean()
                overall_rating = location_data['RATING'].mean()
                overall_sentiment = location_data['OVERALL_SENTIMENT'].mean()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Recent Rating (Last 10)", f"{recent_rating:.2f}", 
                             delta=f"{recent_rating - overall_rating:.2f}")
                with col2:
                    st.metric("Recent Sentiment (Last 10)", f"{recent_sentiment:.3f}", 
                             delta=f"{recent_sentiment - overall_sentiment:.3f}")
                with col3:
                    st.metric("Overall Rating", f"{overall_rating:.2f}")
                with col4:
                    st.metric("Overall Sentiment", f"{overall_sentiment:.3f}")
            else:
                st.info("Not enough data points for trend analysis.")
    
    with tab3:
        st.subheader("Risk Factor Analysis")
        
        # Calculate risk factors across all locations
        risk_factors = analyze_risk_factors(data)
        
        if not risk_factors.empty:
            # Show risk factor distribution
            fig = px.bar(risk_factors, x='Risk Factor', y='Count', 
                        title="Risk Factor Distribution Across Locations",
                        color='Severity', color_discrete_map={'High': 'red', 'Medium': 'orange', 'Low': 'yellow'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Show detailed risk factor breakdown
            st.subheader("Risk Factor Details")
            for _, factor in risk_factors.iterrows():
                with st.expander(f"{factor['Risk Factor']} ({factor['Count']} locations)"):
                    st.write(f"**Severity:** {factor['Severity']}")
                    st.write(f"**Description:** {factor['Description']}")
                    st.write(f"**Impact:** {factor['Impact']}")
        else:
            st.info("No significant risk factors detected.")
    
    with tab4:
        st.subheader("Performance Forecast")
        
        # Simple forecasting based on recent trends
        forecast_data = generate_performance_forecast(data)
        
        if not forecast_data.empty:
            # Show forecast chart
            fig = px.line(forecast_data, x='Date', y='Predicted_Rating', 
                         title="30-Day Performance Forecast",
                         labels={'Predicted_Rating': 'Predicted Rating'})
            fig.add_scatter(x=forecast_data['Date'], y=forecast_data['Confidence_Lower'], 
                           mode='lines', name='Lower Bound', line=dict(dash='dash'))
            fig.add_scatter(x=forecast_data['Date'], y=forecast_data['Confidence_Upper'], 
                           mode='lines', name='Upper Bound', line=dict(dash='dash'))
            st.plotly_chart(fig, use_container_width=True)
            
            # Show forecast summary
            st.subheader("Forecast Summary")
            latest_forecast = forecast_data.iloc[-1]
            st.metric("30-Day Forecast", f"{latest_forecast['Predicted_Rating']:.2f}", 
                     delta=f"{latest_forecast['Predicted_Rating'] - forecast_data.iloc[0]['Predicted_Rating']:.2f}")
        else:
            st.info("Insufficient data for forecasting.")

def calculate_location_risk_metrics(data):
    """Calculate comprehensive risk metrics for each location"""
    location_metrics = []
    
    for location, group in data.groupby('ADDRESS'):
        group = group.sort_values('REVIEW_DATE')
        
        if len(group) < 3:
            continue
        
        # Calculate rolling averages
        group['rolling_rating'] = group['RATING'].rolling(window=7, min_periods=1).mean()
        group['rolling_sentiment'] = group['OVERALL_SENTIMENT'].rolling(window=7, min_periods=1).mean()
        
        # Calculate trends
        rating_trend = group['rolling_rating'].iloc[-1] - group['rolling_rating'].iloc[0]
        sentiment_trend = group['rolling_sentiment'].iloc[-1] - group['rolling_sentiment'].iloc[0]
        
        # Calculate complaint rate (negative sentiment)
        complaint_rate = len(group[group['OVERALL_SENTIMENT'] < 0]) / len(group)
        
        # Calculate recent vs overall performance
        recent_rating = group['RATING'].tail(5).mean()
        recent_sentiment = group['OVERALL_SENTIMENT'].tail(5).mean()
        overall_rating = group['RATING'].mean()
        overall_sentiment = group['OVERALL_SENTIMENT'].mean()
        
        # Calculate risk score
        risk_score = 0
        risk_factors = []
        
        if rating_trend < -0.5:
            risk_score += 2
            risk_factors.append("Declining ratings")
        
        if sentiment_trend < -0.1:
            risk_score += 2
            risk_factors.append("Declining sentiment")
        
        if complaint_rate > 0.2:
            risk_score += 2
            risk_factors.append("High complaint rate")
        
        if recent_rating < overall_rating - 0.5:
            risk_score += 1
            risk_factors.append("Recent performance decline")
        
        if recent_sentiment < overall_sentiment - 0.1:
            risk_score += 1
            risk_factors.append("Recent sentiment decline")
        
        location_metrics.append({
            'Location': location,
            'Total Reviews': len(group),
            'Average Rating': overall_rating,
            'Average Sentiment': overall_sentiment,
            'Rating Trend': rating_trend,
            'Sentiment Trend': sentiment_trend,
            'Complaint Rate': complaint_rate,
            'Recent Rating': recent_rating,
            'Recent Sentiment': recent_sentiment,
            'Risk Score': risk_score,
            'Risk Factors': '; '.join(risk_factors),
            'Last Review Date': group['REVIEW_DATE'].max()
        })
    
    return pd.DataFrame(location_metrics)

def identify_at_risk_locations(location_metrics):
    """Identify locations at risk based on risk score"""
    at_risk = location_metrics[location_metrics['Risk Score'] >= 3].copy()
    at_risk = at_risk.sort_values('Risk Score', ascending=False)
    
    # Format for display
    display_data = []
    for _, row in at_risk.iterrows():
        display_data.append({
            'Location': row['Location'],
            'Risk Score': row['Risk Score'],
            'Risk Factors': row['Risk Factors'],
            'Avg Rating': f"{row['Average Rating']:.2f}",
            'Recent Rating': f"{row['Recent Rating']:.2f}",
            'Rating Trend': f"{row['Rating Trend']:.2f}",
            'Sentiment Trend': f"{row['Sentiment Trend']:.3f}",
            'Complaint Rate': f"{row['Complaint Rate']:.1%}",
            'Total Reviews': row['Total Reviews']
        })
    
    return display_data

def analyze_risk_factors(data):
    """Analyze risk factors across all locations"""
    risk_factors = []
    
    # Define risk factors and their detection logic
    risk_definitions = {
        'Declining Ratings': {
            'description': 'Locations with consistent rating decline',
            'impact': 'High - Direct impact on customer satisfaction'
        },
        'High Complaint Rate': {
            'description': 'Locations with >20% negative sentiment',
            'impact': 'High - Indicates operational issues'
        },
        'Recent Performance Drop': {
            'description': 'Recent ratings significantly below historical average',
            'impact': 'Medium - May indicate temporary or systemic issues'
        },
        'Low Review Volume': {
            'description': 'Locations with very few recent reviews',
            'impact': 'Low - May indicate customer disengagement'
        }
    }
    
    for location, group in data.groupby('ADDRESS'):
        group = group.sort_values('REVIEW_DATE')
        
        if len(group) < 3:
            continue
        
        # Check for declining ratings
        if len(group) >= 7:
            recent_avg = group['RATING'].tail(7).mean()
            overall_avg = group['RATING'].mean()
            if recent_avg < overall_avg - 0.5:
                risk_factors.append('Declining Ratings')
        
        # Check for high complaint rate
        complaint_rate = len(group[group['OVERALL_SENTIMENT'] < 0]) / len(group)
        if complaint_rate > 0.2:
            risk_factors.append('High Complaint Rate')
        
        # Check for recent performance drop
        if len(group) >= 5:
            recent_avg = group['RATING'].tail(5).mean()
            overall_avg = group['RATING'].mean()
            if recent_avg < overall_avg - 0.5:
                risk_factors.append('Recent Performance Drop')
        
        # Check for low review volume
        days_since_last = (datetime.now() - group['REVIEW_DATE'].max()).days
        if days_since_last > 30:
            risk_factors.append('Low Review Volume')
    
    # Count risk factors
    factor_counts = {}
    for factor in risk_factors:
        factor_counts[factor] = factor_counts.get(factor, 0) + 1
    
    # Create DataFrame
    risk_data = []
    for factor, count in factor_counts.items():
        severity = 'High' if count > len(data['ADDRESS'].unique()) * 0.3 else 'Medium' if count > len(data['ADDRESS'].unique()) * 0.1 else 'Low'
        risk_data.append({
            'Risk Factor': factor,
            'Count': count,
            'Severity': severity,
            'Description': risk_definitions[factor]['description'],
            'Impact': risk_definitions[factor]['impact']
        })
    
    return pd.DataFrame(risk_data)

def generate_performance_forecast(data):
    """Generate simple performance forecast based on recent trends"""
    if data.empty:
        return pd.DataFrame()
    
    # Calculate overall trend
    data_sorted = data.sort_values('REVIEW_DATE')
    recent_data = data_sorted.tail(30)  # Last 30 days
    
    if len(recent_data) < 5:
        return pd.DataFrame()
    
    # Simple linear trend
    recent_data['days'] = (recent_data['REVIEW_DATE'] - recent_data['REVIEW_DATE'].min()).dt.days
    recent_data['days'] = recent_data['days'].fillna(0)
    
    # Calculate trend
    avg_rating = recent_data['RATING'].mean()
    if len(recent_data) > 1:
        rating_trend = np.polyfit(recent_data['days'], recent_data['RATING'], 1)[0]
    else:
        rating_trend = 0
    
    # Generate forecast
    forecast_dates = pd.date_range(start=data_sorted['REVIEW_DATE'].max(), periods=31, freq='D')[1:]
    forecast_data = []
    
    for i, date in enumerate(forecast_dates):
        predicted_rating = avg_rating + (rating_trend * (i + 1))
        confidence_interval = 0.5  # Simple confidence interval
        
        forecast_data.append({
            'Date': date,
            'Predicted_Rating': max(1, min(5, predicted_rating)),
            'Confidence_Lower': max(1, min(5, predicted_rating - confidence_interval)),
            'Confidence_Upper': max(1, min(5, predicted_rating + confidence_interval))
        })
    
    return pd.DataFrame(forecast_data)
