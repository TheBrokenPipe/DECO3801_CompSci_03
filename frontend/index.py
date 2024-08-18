# an example page
import streamlit as st
# TODO: import backend


# retrieving stuff from backend and add to history
def get_chat_response():
    response = "Response!"
    st.session_state.messages.append({"role": "assistant", "content": response})
    # TODO: get stuff from the backend
    return response


# gets an array of dictionaries with keys:
#  - role (the role of the message (user, assistant))
#  - content (the message to display)
def get_chat_history():
    return st.session_state.messages


# sending suff to the backend
def send_transcript(transcript):
    return  # TODO


def send_doc(doc):
    return  # TODO


# role is user or assistant - also adds to history
def send_message(content):
    st.session_state.messages.append({"role": "user", "content": content})


# constants
CHAT_PROMPT = "Ask a question about your meetings"  # TODO: confirm with group

# set up
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in get_chat_history():
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# display input box
chat_input = st.chat_input(CHAT_PROMPT)

# React to user input
if chat_input:
    # Display user message in chat message container
    st.chat_message("user").markdown(chat_input)
    # Add user message to chat history
    send_message(chat_input)

    response = get_chat_response()
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
