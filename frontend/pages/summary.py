# allowing to work with the intergace in parent directory
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# other imports
import streamlit as st
from datetime import datetime
import random
from interface import *

if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = 0

chat = server.chats[st.session_state["current_chat"]]

back_button = st.button("🔙", key="backButton")

if (back_button):
    st.switch_page("pages/chat.py")

topics = chat.get_topics()

topicsNames = map(lambda topic: topic.get_name(), topics)
headertxt = " and ".join(topicsNames) + " Summary"
st.header(headertxt)

# topicModified = map(lambda topic: topic.get_modified_time(), topics)
# st.text(f"Last modified: " + datetime.strftime(max(topicModified), "%Y-%m-%d"))

col1, col2 = st.columns(2)

with col1:
    with st.expander("Summary", expanded=True):
        st.write(chat.get_summary())

    with st.expander("Action Items", expanded=True):
        for actionItem in chat.get_action_items():
            st.markdown(f" - {actionItem}")

# TODO: change to allow for multiple meetings
allMeetings = chat.get_topics()[0].get_meetings()

with col2.expander("Recent Meetings", expanded=True):
    for meeting in allMeetings:
        meetingContainer = st.container(border=True)
        meetingContainer.write(meeting.get_meeting_name())
        meetingContainer.write(        
            datetime.strftime(
                meeting.date,
                "%d/%m/%y"
            )
        )
        bcol1, bcol2, bcol3 = meetingContainer.columns(3)  # button columns
        bcol1.button("Media")
        bcol2.button("Transcript")
        bcol3.button("Remove")
