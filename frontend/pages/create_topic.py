import streamlit as st
from interface import *
import streamlit_tags as stt

col1, col2 = st.columns([6, 1], gap = "large", vertical_alignment="center")
with col1:
    if st.button('← Back'):
        st.switch_page("pages/upload_meeting.py")

with col2:
    if st.button('Help'):
        st.switch_page("pages/help.py")

topics = asyncio.run(server.get_all_topics())

# with st.expander("Current Topics"):
    # for topic in topics:
        # st.write(topic.get_name())

st.title("Create New Topic")

meeting_name = st.text_input("New topic name:")

existing_meetings = asyncio.run(server.get_all_meetings())

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
    wanted_meetings = []
    for name in existing:
        for meeting in existing_meetings:
            if meeting.get_meeting_name().lower() == name.lower():
                wanted_meetings.append(meeting)
    server.create_topic(meeting_name, wanted_meetings)
