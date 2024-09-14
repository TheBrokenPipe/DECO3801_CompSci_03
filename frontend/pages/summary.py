# allowing to work with the intergace in parent directory
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# other imports
import streamlit as st
import datetime
import random
from interface import *

if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = 0

chat = server.get_user("user").get_chats()[st.session_state["current_chat"]]

topicsNames = map(lambda topic: topic.get_name(), chat.get_topics())
headertxt = " and ".join(topicsNames) + " Summary"
st.header(headertxt)

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
            datetime.datetime.strftime(
                meeting.get_meeting_date(),
                "%d/%m/%y"
            )
        )
        bcol1, bcol2, bcol3 = meetingContainer.columns(3)  # button columns
        bcol1.button(key=random.randint(0, 10000), label="Media")
        bcol2.button(key=random.randint(10000, 20000), label="Transcript")
        bcol3.button(key=random.randint(20000, 30000), label="Remove")
