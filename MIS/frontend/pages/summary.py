
# other imports
import streamlit as st
from datetime import datetime
import random
import asyncio
from MIS.frontend.interface import Server

if "current_chat_id" not in st.session_state:
    st.session_state["current_chat_id"] = asyncio.run(Server.get_latest_chats()).id

chat = asyncio.run(Server.get_chat_by_id(st.session_state["current_chat_id"]))


if "transcript_view_id" not in st.session_state:
    st.session_state["transcript_view_id"] = -1

print("Summary State:", st.session_state["summarise_chat"])

def transcript_click(index):
    st.session_state["transcript_view_id"] = index


back_button = st.button("🔙", key="backButton")

if back_button:
    st.switch_page("pages/chat.py")

topics = asyncio.run(chat.topics)


topicsNames = map(lambda topic: topic.name, topics)
headertxt = " and ".join([t.name for t in topics]) + " Summary"
st.header(headertxt)

# topicModified = map(lambda topic: topic.get_modified_time(), topics)
# st.text(f"Last modified: " + datetime.strftime(max(topicModified), "%Y-%m-%d"))

col1, col2 = st.columns(2)

with col1:
    with st.expander("Summary", expanded=True):
        print(f"Session State: {st.session_state['summarise_chat']}")
        if not st.session_state["summarise_chat"]:
            st.write(chat.summary)
            st.session_state["summarise_chat"] = True

    with st.expander("Action Items", expanded=True):
        for actionItem in asyncio.run(chat.action_items):
            st.markdown(f" - {actionItem}")

# TODO: change to allow for multiple meetings
allMeetings = asyncio.run(chat.meetings)
transcript_buttons = []

with col2.expander("Recent Meetings", expanded=True):
    for meeting in allMeetings:
        meetingContainer = st.container(border=True)
        bcol1, bcol2 = meetingContainer.columns(2)  # button columns
        with bcol1:
            st.write(meeting.name)
            st.write(
                datetime.strftime(
                    meeting.date,
                    "%d/%m/%y"
                )
            )
        with bcol2:
            transcript_buttons.append(
                st.button(
                    "Transcript", on_click=transcript_click,
                    kwargs={"index": meeting.id}, key=f"TR-{meeting.id}"
                )
            )
            # st.button("Media", k)
            # bcol3.button("Remove")

if any(transcript_buttons):
    st.switch_page("pages/transcript_view.py")
