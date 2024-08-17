# an example page
import streamlit as st
# TODO: import backend


# retrieving stuff from backend
def get_chat_response():
    # TODO: get stuff from the backend
    return "Response!"


# sending suff to the backend
def send_transcript(transcript):
    return  # TODO


def send_doc(doc):
    return  # TODO


def send_message(message):
    return  # TODO


st.write("Hello world")

with st.chat_message("user"):
    st.write("Hello 👋")

uploaded_files = st.file_uploader(
    "Choose a CSV file", accept_multiple_files=True
)
for uploaded_file in uploaded_files:
    bytes_data = uploaded_file.read()
    st.write("filename:", uploaded_file.name)
    st.write(bytes_data)