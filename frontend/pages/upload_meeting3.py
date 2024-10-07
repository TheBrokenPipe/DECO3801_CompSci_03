import streamlit as st
import streamlit_tags as stt
from interface import Server

# known issue: the warning about consent only occurs twice.

default_password = "password123"

if "tried_submit" not in st.session_state:
    st.session_state["tried_submit"] = False

col1, col2 = st.columns([6, 1], gap="large", vertical_alignment="center")
with col1:
    if st.button('← Back', key="backTo2"):
        st.switch_page("pages/upload_meeting2.py")

# a list of all the usernames in the server.
userNames = list(map(lambda user: user.get_name(), server.get_users()))

# a list of all the topics in the server.
topicNames = list(map(lambda topic: topic.get_name(), server.get_topics()))

# page content
attendeeNames = stt.st_tags(
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

consent = st.checkbox(
    "The attendees consent to this meeting being uploaded and visible to all people can see the tags",
    key="wevsj"
)

if st.session_state["tried_submit"]:
    st.warning(
        "Please get consent from participants or reduce who you're sharing the video with."
    )

col1, col2, col3 = st.columns([1, 4, 1], gap="large", vertical_alignment="top")
with col1:
    if st.button("Previous", key="previous"):
        st.switch_page("pages/upload_meeting2.py")

with col2:
    st.write("")

submit = col3.button("Submit", key="submit")

if submit and consent:
    # get information from upload form page 1
    meeting_name = st.session_state["new_meeting_name"]
    meeting_date = st.session_state["new_meeting_date"]
    main_file = st.session_state["new_meeting_file"]

    # get information from upload for page 2
    supporting_file = st.session_state["new_meeting_supporting_file"]

    # a helper function to get user if exist or crete a new one
    def get_create_user(name):
        result = server.get_user(name)
        if (result is None):
            # the user does not exist, so we create it
            result = server.create_user(name, default_password)
        return result

    result = server.upload_meeting(
        data=main_file.read(),
        filename=main_file.name,
        name=meeting_name,
        date=meeting_date,
        attendees=list(map(get_create_user, attendeeNames)),
        callback=updateSummary
    )

    st.switch_page("pages/chat.py")
    st.session_state["tried_submit"] = False

if submit and not consent:
    st.session_state["tried_submit"] = True
