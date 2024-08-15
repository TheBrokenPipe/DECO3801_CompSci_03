# an example page
import streamlit as st
# TODO: import backend
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