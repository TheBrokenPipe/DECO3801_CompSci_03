import streamlit as st
import streamlit_tags as stt
from index import pages
from interface import server

col1, col2 = st.columns([6, 1], gap="large", vertical_alignment="center")
with col1:
    if st.button('← Back', key="backTo2"):
        st.switch_page(pages["upload_meeting2"])

# a list of all the usernames in the server.
userNames = list(map(lambda user: user.get_name(), server.get_users()))

# a list of all the topics in the server.
topicNames = list(map(lambda topic: topic.get_name(), server.get_topics()))

# page content goes here
attendees = stt.st_tags(
    label='Meeting attendees',
    text='Press enter to add more',
    value=[],
    suggestions=userNames,
    key="aljnf")

topics = stt.st_tags(
    label='Meeting topics',
    text='Press enter to add more',
    value=[],
    suggestions=topicNames,
    key="sdwbh")

col1, col2, col3 = st.columns([1, 4, 1], gap="large", vertical_alignment="top")
with col1:
    if st.button("← Back", key="previous"):
        st.switch_page(pages["upload_meeting2"])

with col2:
    st.write("")

with col3:
    if st.button("Submit", key="submit"):
        st.switch_page(pages["chat"])