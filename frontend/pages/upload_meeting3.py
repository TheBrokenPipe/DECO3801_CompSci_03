import streamlit as st
import streamlit_tags as stt
from index import pages
from interface import server

# known issue: the warning about consent only occurs twice.

if "tried_submit" not in st.session_state:
    st.session_state["tried_submit"] = False

col1, col2 = st.columns([6, 1], gap="large", vertical_alignment="center")
with col1:
    if st.button('← Back', key="backTo2"):
        st.switch_page(pages["upload_meeting2"])

# a list of all the usernames in the server.
userNames = list(map(lambda user: user.get_name(), server.get_users()))

# a list of all the topics in the server.
topicNames = list(map(lambda topic: topic.get_name(), server.get_topics()))

# page content
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

consent = st.checkbox("The attendees consent to this meeting being uploaded and \
                      visible to all people can see the tags", key="wevsj")

if st.session_state["tried_submit"]:
    st.warning("Please get consent from participants or reduce who you're sharing \
                 the video with.")

col1, col2, col3 = st.columns([1, 4, 1], gap="large", vertical_alignment="top")
with col1:
    if st.button("← Back", key="previous"):
        st.switch_page(pages["upload_meeting2"])

with col2:
    st.write("")

submit = col3.button("Submit", key="submit")

if submit and consent:
    st.switch_page(pages["chat"])
    st.session_state["tried_submit"] = False

if submit and not consent:
    st.session_state["tried_submit"] = True
