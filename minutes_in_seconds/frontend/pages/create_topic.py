import streamlit as st
from minutes_in_seconds.frontend.interface import Server
import streamlit_tags as stt
import asyncio

col1, col2 = st.columns([6, 1], gap="large", vertical_alignment="center")
with col1:
    if st.button('← Back'):
        st.switch_page("pages/chat.py")

with col2:
    if st.button('Help'):
        st.switch_page("pages/help.py")

topics = asyncio.run(Server.get_all_topics())

with st.expander("Current Topics"):
    for topic in topics:
        st.write(topic.name)

st.title("Create New Topic")

meeting_name = st.text_input("New topic name:")

existing_meetings = asyncio.run(Server.get_all_meetings())

selected_meetings = stt.st_tags(
    label='Existing Meetings',
    text='Press enter to add more',
    value=[],
    suggestions=[m.name for m in existing_meetings],
    key="hello"
)

want_create = st.button("Create")

if want_create:
    selected_meetings = [sm.lower() for sm in selected_meetings]

    asyncio.run(
        Server.create_topic(
            meeting_name,
            [m for m in existing_meetings if m.name.lower() in selected_meetings]
        )
    )

    st.switch_page("pages/chat.py")
