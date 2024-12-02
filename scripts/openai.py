import streamlit as st
import pandas as pd
import datetime
import os

from PIL import Image
from io import BytesIO
from openai import OpenAI
from tempfile import gettempdir

from scripts.sapi import write_table

client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

def generate_response(prompt):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred during content generation. Please try again.")
        return ''


def assistant(file_id, assistant_id, data):
    if st.session_state.thread_id is None:
    
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": (
                        "To help you navigate the CSV file, here is the description of some important columns: "
                        "feedback_id: Unique identifier for the feedback. "
                        "feedback_channel: Source channel of the feedback (e.g., platform or app). "
                        "place_id: Unique identifier for the place being reviewed. "
                        "address: Address of the place. "
                        "place_total_score: The total score of the place based on reviews. "
                        "place_rev_count: Number of reviews for the place. "
                        "latitude/longitude: Geographical coordinates of the place. "   
                        "customer_name: Name of the customer. "
                        "reviewer_rev_count: Number of reviews by the reviewer. "
                        "feedback_date: Date when the feedback was given. " 
                        "rating: The rating given by the reviewer (on a scale). "
                        "review_content_meal_type: Type of meal mentioned in the review. "
                        "review_content_service_type: Type of service mentioned. "
                        "review_content_food/service/atmosphere: Specific ratings for food, service, and atmosphere. "  
                        "review_text: Text content of the review. "
                        "sentiment: Sentiment analysis result for the feedback (e.g., positive, negative). "
                        "city/state/postalCode: Location details of the place."
                    ),
                    "attachments": [
                        {
                        "file_id": file_id, #file.id,
                        "tools": [{"type": "code_interpreter"}]
                        }
                    ]
                }
            ]
        )
        st.session_state.thread_id = thread.id

    if not st.session_state.table_written:
        df_log = pd.DataFrame({
            'thread_id': [st.session_state.thread_id],
            'created_at': [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        })

        write_table(table_id='in.c-257-bot-log.logging', df=df_log, is_incremental=True)
        st.session_state.table_written = True

    with st.expander("Data"):
        data_to_display = data.copy()
        data_to_display.drop(columns=['REVIEW_ID', 'ID', 'FEEDBACK_ID', 'PLACE_ID', 'STREET', 'CITY', 'STATE', 'POSTAL_CODE', 'REVIEWER_NAME', 'CUSTOMER_ID', 'REVIEWER_ID', 'REVIEWER_URL', 'REVIEWER_NUM_OF_REVIEWS', 'REVIEW_DATE', 'EVENT_DATE', 'FEEDBACK_ORIGINAL_TEXT', 'REVIEW_TEXT'], errors='ignore', inplace=True)
        st.dataframe(data_to_display)
        st.caption(f'Thread ID: {st.session_state.thread_id}')


    for message in st.session_state.messages:
        if message["role"] == "user":
            avatar = '🧑‍💻'
        else:
            avatar = st.secrets['MINI_LOGO_URL']
        
        with st.chat_message(message["role"], avatar=avatar):
            if "[Image:" in message["content"]:
                start_index = message["content"].find("[Image:") + len("[Image: ")
                end_index = message["content"].find("]", start_index)
                image_path = message["content"][start_index:end_index]
                st.image(image_path)
                
                text_content = message["content"][:start_index - len("[Image: ")] + message["content"][end_index + 1:]
                st.markdown(text_content)
            else:
                st.markdown(message["content"])
        placeholder = st.empty()
    styl = f"""
        <style>
            .stTextInput {{
                position: fixed;
                bottom: 1rem; /* Stick to the bottom of the viewport */
                background-color: white; /* Set background color to white */
                z-index: 1000; /* Bring the text input to the front */
                padding: 10px; /* Add some padding for aesthetics */
            }}
            .spacer {{
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                height: 2rem; /* Height of the spacer */
                background-color: #ffffff; /* Color of the spacer */
                z-index: 999; /* Ensure it's behind the text input */
            }}
            .wait-note {{
                position: fixed;
                bottom: 0.2rem;
                left: 50%;
                transform: translateX(-50%);
                font-size: 12px;
                color: #666;
                font-style: italic;
                z-index: 1001;
            }}
        </style>
        """
    st.markdown(styl, unsafe_allow_html=True)
    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)  # Add the spacer div

    text_input = st.text_input("Query", placeholder="Your query", label_visibility='collapsed')
    if prompt := text_input:
        with placeholder.container():
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar='🧑‍💻'):
                st.markdown(prompt)

            with st.spinner('Analyzing...'):  
                thread_message = client.beta.threads.messages.create(
                    st.session_state.thread_id,
                    role="user",
                    content=prompt,
                )
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=st.session_state.thread_id,
                    assistant_id=assistant_id,
                )

            if run.status == 'completed':
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                newest_message = messages.data[0]
                complete_message_content = ""
                with st.chat_message("assistant", avatar=st.secrets['MINI_LOGO_URL']):
                    for message_content in newest_message.content:
                        if hasattr(message_content, "image_file"):
                            file_id = message_content.image_file.file_id

                            resp = client.files.with_raw_response.retrieve_content(file_id)

                            if resp.status_code == 200:
                                image_data = BytesIO(resp.content)
                                img = Image.open(image_data)
                                
                                temp_dir = gettempdir()
                                image_path = os.path.join(temp_dir, f"{file_id}.png")
                                img.save(image_path)
                        
                                st.image(img)
                                complete_message_content += f"[Image: {image_path}]\n"

                        elif hasattr(message_content, "text"):
                            text = message_content.text.value
                            st.markdown(text)
                            complete_message_content += text + "\n"

                st.session_state.messages.append({"role": "assistant", "content": complete_message_content})

            else:
                st.write(f"Run status: {run.status}")