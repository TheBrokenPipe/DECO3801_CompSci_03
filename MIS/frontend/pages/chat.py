import time
import streamlit as st
import asyncio
from datetime import datetime, time, timedelta

from st_screen_stats import ScreenData
from MIS.frontend.interface import Server

print("Loading Chat")

def btn_click(index):
    st.session_state["current_chat_id"] = index


chats = asyncio.run(Server.get_all_chats())
# print(chats[0].history)
if len(chats) == 0:
    asyncio.run(Server.create_chat("First Chat", []))
    chats = asyncio.run(Server.get_all_chats())

# chat_names = []
# for chat in chats:
#     chat_names.append(chat._chat.name)

if "current_chat_id" not in st.session_state:
    st.session_state["current_chat_id"] = asyncio.run(Server.get_latest_chats()).id
if "transcript_view_id" not in st.session_state:
    st.session_state["transcript_view_id"] = asyncio.run(Server.get_latest_chats()).id
    st.session_state["transcript_view_id_old"] = asyncio.run(Server.get_latest_chats()).id
else:
    if st.session_state["transcript_view_id"] != st.session_state["transcript_view_id_old"]:
        st.session_state["transcript_view_id_old"] = st.session_state["transcript_view_id"]
        st.switch_page("pages/transcript_view.py")


print(st.session_state["current_chat_id"])

# col1, col2 = st.columns(2)  # button columns


# with col1:
screenD = ScreenData(setTimeout=1500)
screen_d = screenD.st_screen_data()

current_chat = asyncio.run(Server.get_chat_by_id(st.session_state["current_chat_id"]))
st.title(current_chat.name)
chat_container = st.container(border=True, height=int(screen_d["innerHeight"] * 0.62))

for message in current_chat.history:
    # print(message)
    chat_container.chat_message(message["username"]).markdown(message["message"])
chat_input = st.chat_input("Ask a question about your meetings")


latest_meetings = asyncio.run(Server.get_all_meetings())

# with col2:
#     current_chat = asyncio.run(Server.get_chat_by_id(st.session_state["current_chat_id"]))
#     st.title("Your Feed")
#     feed_container = st.container(border=True)
#
#     for meeting in latest_meetings:
#         st.text(meeting.name)
#         # print(message)
#         # feed_container.chat_message(message["username"]).markdown(message["message"])


with st.sidebar:
    st.title("Chats")

    with st.expander("Chats", True):
        new_chat_button = st.button("New Chat")
        summary_button = st.button("Chat Summary")
        st.divider()
        for chat in chats:
            if chat.id == st.session_state["current_chat_id"]:
                st.text(chat.name)
            else:
                st.button(chat.name, on_click=btn_click, kwargs={"index": chat.id})

    st.divider()
    with st.expander("Actions", True):
        upload_button = st.button("Upload Meeting")
        new_topic_button = st.button("Create Topic")


def source_btn_click(index):
    print("source_btn_click")
    st.session_state["transcript_view_id"] = index


source_buttons = []

# React to user input
if chat_input:
    chat_container.chat_message("User").markdown(chat_input)
    add_chat = asyncio.run(current_chat.add_message("User", chat_input))
    waiting_message = chat_container.chat_message("Assistant").markdown("Lemme see...")
    response, sources = asyncio.run(current_chat.send_message(chat_input))

    asyncio.run(current_chat.add_message("Assistant", response))
    chat_container.chat_message("Assistant").markdown(response)
    chat_container.chat_message("Assistant").markdown(f"Sources:\n" + "\n".join(list({source["meeting"].name for source in sources})))
    columns = st.columns(min(5, len(sources)))  # button columns
    for index, source in enumerate(sources):
        with columns[index]:
            # hours, remainder = divmod(source["start_time"], 3600)
            # minutes, seconds = divmod(remainder, 60)
            # start_time = time(hour=int(hours), minute=int(minutes), second=int(seconds))
            # + start_time.strftime("%H:%M:%S" if hours > 0 else "%M:%S")
            st.button(
                source["meeting"].name + " " + (source["start_time"]),
                on_click=source_btn_click, kwargs={"index": source["meeting"].id}, key=source["key"]
            )

if new_chat_button:
    st.switch_page("pages/create_chat.py")

if summary_button:
    st.session_state["summarise_chat"] = False
    print("Chat State:", st.session_state["summarise_chat"])
    st.switch_page("pages/summary.py")

if upload_button:
    st.switch_page("pages/upload_meeting.py")

if new_topic_button:
    st.switch_page("pages/create_topic.py")

