import streamlit as st

def introduction():
    st.title('Keboola QSR 360 Solution')
    st.write("Own your data, automate workflows, and drive smarter decisions across all restaurant initiatives.")
    
    col1, col2 = st.columns([0.4, 0.6], gap='large', vertical_alignment='center')
    with col1:
        st.markdown("<strong>Keboola’s QSR 360</strong> is revolutionizing the franchise business by seamlessly integrating data, automating workflows, and providing advanced analytics for enhanced operational efficiency and strategic decision-making.", unsafe_allow_html=True)
    with col2:
        st.image("https://i.ibb.co/jysDwBP/66bdc321b8987869a60f9d1b-QSR-diagram-2-2.jpg")
    
    st.divider()
    st.subheader('Demo: Customer Voice and AI Support')
    st.markdown("""
        Use powerful AI analysis to improve service quality and customer satisfaction. Analyzing feedback helps identify areas for improvement, ensuring high service standards.
        \n\nThe demo environment includes the following sections:
        \n\n1. The **Locations** tab provides a visual representation of restaurant locations on a map, allowing users to explore geographical data related to customer reviews. It aggregates review scores and counts for each location, helping teams identify which areas are performing well and which may need attention.
        \n\n2. The **Overview** tab provides instant, out-of-the-box insights into online reviews for all your restaurant locations. It delivers a comprehensive overview of general ratings, key trends, and identifies any anomalies in customer feedback. The app's easy-to-use interface allows teams to quickly assess the overall sentiment across various locations, helping them stay on top of evolving customer perceptions.
        \n\n3. The **AI Analysis** tab is a powerful tool designed to analyze customer reviews by utilizing advanced AI-driven sentiment analysis. The app categorizes feedback into key areas, breaking down each category into subgroups and specific topics to provide deep insights into customer sentiment. This structured approach helps businesses understand detailed feedback patterns and address specific areas of concern or praise.
        \n\nHere’s an example of how the app organizes the analysis:
        \n\n- **Category:** Broad themes identified in customer reviews (e.g., Food, People, Experience)
        \n\n- **Group:** More specific aspects of the category (e.g., Quality, Team, Ordering)
        \n\n- **Topics:** Fine-grained details mentioned by customers (e.g., Taste, Hospitality, Pricing Accuracy)
        \n\nThis in-depth analysis allows teams to pinpoint specific trends in customer sentiment, improving operational decision-making and enhancing overall customer satisfaction by responding to the most critical feedback efficiently.
        \n\n4. The **Support** tab is an interactive tool designed to assist Customer Support teams in efficiently managing guest communication through AI-generated review replies. These AI-crafted responses are carefully reviewed and approved by the team, ensuring quality and personalization. Using a funnel or mailbox-style interface, the app facilitates team collaboration, enabling swift responses to both positive and negative feedback. By streamlining this process, the app helps boost guest satisfaction and loyalty, ensuring timely and thoughtful engagement with all customer reviews.
        \n\n5. The **Assistant** tab provides an interactive chat experience with an AI assistant, allowing you to engage with your data and receive insights in real-time.
    """, unsafe_allow_html=True)