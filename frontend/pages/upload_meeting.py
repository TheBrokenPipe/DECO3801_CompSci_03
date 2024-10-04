# # allowing to work with the intergace in parent directory
# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from interface import Server
import asyncio

want_back = None

col1, col2 = st.columns([6, 1], gap="large", vertical_alignment="center")
with col1:
    want_back = st.button('← Back')

with col2:
    if st.button('Help'):
        st.switch_page("pages/help.py")

st.write('Welcome! To start uploading your meeting, please give the meeting a unique name and upload the transcript/recording from your computer')

meeting_name = st.text_input("Enter the name of the meeting:")

meeting_date = st.date_input("On what date did the event take place?", format="DD/MM/YYYY")

uploaded_file = st.file_uploader("Upload Recording/Transcript", type=['mp3', 'mp4', 'txt', 'wav'])

if uploaded_file is not None:
    st.write(f"{meeting_name} uploaded successfully.")

col1, col2 = st.columns([6.5, 1], gap="large", vertical_alignment="top")
with col1:
    st.write("")

with col2:
    next1 = st.button("Next", key="NextFromUpload1")

if next1:
    asyncio.run(Server.upload_meeting(meeting_name, meeting_date, uploaded_file))
    st.switch_page("pages/chat.py")

    # TODO skipping the rest to make this work
    if uploaded_file:
        st.session_state["new_meeting_name"] = meeting_name
        st.session_state["new_meeting_date"] = meeting_date
        st.session_state["new_meeting_file"] = uploaded_file
        st.switch_page("pages/upload_meeting2.py")
    else:
        st.warning("Please upload a main meeting file")

# if st.button("Next", key = "next_buttonB"):
#         st.session_state.page = "upload_page2"

# if st.session_state.page == "upload_page1":
#     upload_page1()

if want_back:
    st.switch_page("pages/chat.py")