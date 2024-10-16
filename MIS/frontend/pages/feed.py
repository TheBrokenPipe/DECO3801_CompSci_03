import streamlit as st
import asyncio

from MIS.frontend.interface import Server, Meeting, Topic
from annotated_text import annotated_text

print("Loading Feed")
if "current_chat_id" in st.session_state:
    st.switch_page("pages/chat.py")
if "transcript_view_id" in st.session_state:
    st.switch_page("pages/transcript_view.py")


def transcript_btn_click(index):
    st.session_state["transcript_view_id"] = index


def chat_btn_click(index):
    st.session_state["current_chat_id"] = index


# # GET MEETINGS
async def get_top_meetings() -> list[Meeting]:
    # Retrieve all meetings
    meetings = await Server.get_all_meetings()
    # Sort meetings by id in descending order and limit to the first 10
    sorted_meetings = sorted(
        meetings, key=lambda meeting: meeting.id, reverse=True
    )[:10]
    return sorted_meetings

# # SET TOPIC COLOURS
all_topics = asyncio.run(Server.get_all_topics())
colours = ["#093", "#36F", "#C09", "#90C", "#C60"]
topic_colours = {}
for i, topic in enumerate(all_topics):
    topic_colours[topic.name] = colours[i % len(colours)]

latest_meetings = asyncio.run(get_top_meetings())

# # MAKE FEED
st.title("Your Feed")
if latest_meetings:
    transcript_buttons = []

    def format_topics(topics: list[Topic]) -> list:
        return [(topic.name, "topic", topic_colours[topic.name])
                for topic in topics]

    for meeting in latest_meetings:
        st.write("")
        col1, col2 = st.columns([4, 1], gap="large",
                                vertical_alignment="center")
        with col1:
            st.header(meeting.name)
        with col2:
            st.button(
                "Transcript", on_click=transcript_btn_click,
                kwargs={"index": meeting.id}, key=meeting.id
            )
        topics = asyncio.run(meeting.topics)
        annotated_text(*format_topics(topics))
        st.write(meeting.summary)

        action_items = asyncio.run(meeting.action_items)

        with st.expander("Action Items"):
            items_markdown = "\n".join(f"- {item}" for item in action_items)
            st.markdown(items_markdown)

else:
    st.write(
        """
        ### You have no meetings yet!
        """
    )

# # MAKE SIDE BAR
chats = asyncio.run(Server.get_all_chats())

with st.sidebar:
    st.button("Home", icon=":material/home:", key="home")

    with st.expander("Chats", True):
        new_chat_button = st.button("New Chat", key="new_chat")
        summary_button = st.button("Chat Summary", key="chat_summary",
                                   disabled=True)
        if chats:
            st.divider()
            for chat in chats:
                st.button(chat.name, on_click=chat_btn_click,
                          kwargs={"index": chat.id}, key="chat" + str(chat.id))

    with st.expander("Actions", True):
        upload_button = st.button("Upload Meeting", key="upload")
        new_topic_button = st.button("Create Topic", key="new_topic")

# # SET BUTTONS
if new_chat_button:
    st.switch_page("pages/create_chat.py")

if upload_button:
    st.switch_page("pages/upload_meeting.py")

if new_topic_button:
    st.switch_page("pages/create_topic.py")
