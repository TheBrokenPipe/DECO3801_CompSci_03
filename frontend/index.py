# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# an example page
import streamlit as st
# from manager import Thingo
from interface import *
# from dotenv import load_dotenv

# load_dotenv()

# manager = Thingo(10)


# retrieving stuff from backend and add to history
def get_chat_response(query_text):
    response = manager.query(query_text)
    st.session_state.messages.append({"role": "assistant", "content": response})
    # TODO: get stuff from the backend
    return response


# gets an array of dictionaries with keys:
#  - role (the role of the message (user, assistant))
#  - content (the message to display)
def get_chat_history():
    return st.session_state.messages


# sending suff to the backend
def send_audio(transcript):
    print(transcript)
    print(type(transcript))
    manager.upload_file_from_streamlit(transcript)
    return
    st.write("audio sent")
    manager.add_audio_meeting_transcript_document()
    return  # TODO


def send_doc(doc):
    st.write("doc sent")
    return  # TODO


# role is user or assistant - also adds to history
def send_message(content):
    st.session_state.messages.append({"role": "user", "content": content})

user = server.get_users()[1]
chats = user.get_chats()

chat_names = []
for chat in chats:
    chat_names.append(chat.get_topics()[0].get_name())

def btn_click(index):
    for message in chats[index].get_messages():
        # print(message.get_sender())
        with st.chat_message(message.get_sender().get_name()):
        # with st.chat_message("Me"):
            st.markdown(message.get_text())

for i in range(len(chat_names)):
    st.sidebar.button(chat_names[i], on_click=btn_click, args=[i])




# add_selectbox = st.sidebar.selectbox(
    # "Which chat?",
    # tuple(chat_names)
# )


# constants
CHAT_PROMPT = "Ask a question about your meetings"  # TODO: confirm with group
AUDIO_TYPES = ("mp3", "wav", "m4a")
SUPPORTING_MEDIA_TYPES = ("txt",)

# set up
if "messages" not in st.session_state:
    st.session_state.messages = []

# uploading files
uploadForm = st.form("uploadform", clear_on_submit=True)

upload1, upload2 = uploadForm.columns(2)
#  - uploading audio files
uploaded_audio = upload1.file_uploader(
    label="Upload meeting transcription",
    accept_multiple_files=True,
    type=list(AUDIO_TYPES)
) 

#  - uploading supporting files
supporting_docs = upload2.file_uploader(
    label="Uploading supporting text documents",
    accept_multiple_files=True,
    type=list(SUPPORTING_MEDIA_TYPES)
)

submitFiles = uploadForm.form_submit_button("Upload audio and documents")

if submitFiles:
    for uploaded_audio in uploaded_audio:
        send_audio(uploaded_audio)

    for doc in supporting_docs:
        send_doc(doc)

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

    response = get_chat_response(chat_input)
    # Display assistant response in chat message container
    st.chat_message("assistant").markdown(response)
