import streamlit as st
from interface import *
from index import pages
import streamlit_tags as stt

col1, col2 = st.columns([6, 1], gap = "large", vertical_alignment="center")
with col1:
    if st.button('← Back'):
        st.switch_page(pages["upload_meeting"])

with col2:
    if st.button('Help'):
        st.switch_page(pages["help"])

topics = server.get_topics()

with st.expander("Current Topics"):
    for topic in topics:
        st.write(topic.get_name())

st.title("Create New Topic")

meeting_name = st.text_input("New topic name:")

existing_meetings = server.get_meetings()

existing_meeting_names = []
for meeting in existing_meetings:
    existing_meeting_names.append(meeting.get_meeting_name())

existing = stt.st_tags(
    label='Existing Meetings',
    text='Press enter to add more',
    value=[],
    suggestions=existing_meeting_names,
    key="hello")

users = stt.st_tags(
    label='Users',
    text='Press enter to add more',
    value=[],
    suggestions=[],
    key="ctfyvg")

want_create = st.button("Create")

if want_create:
    server.create_topic(meeting_name, [], [])
