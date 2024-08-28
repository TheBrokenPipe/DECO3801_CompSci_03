import streamlit as st
from streamlit_chat import message

# Function to generate a response (You can replace this with an actual AI model)
def generate_response(user_input):
    return f"Echo: {user_input}"

# Streamlit app
st.title("Basic Chatbot")

# Session state to store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# User input
user_input = st.text_input("You: ", key="input")

# Generate response when the user submits input
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    response = generate_response(user_input)
    st.session_state.messages.append({"role": "bot", "content": response})

# Display chat history
for message_data in st.session_state.messages:
    if message_data["role"] == "user":
        message(message_data["content"], is_user=True)
    else:
        message(message_data["content"])

