import time
import streamlit as st
import asyncio
from interface import Server

print("Loading Chat")

def btn_click(index):
    st.session_state["current_chat_id"] = index


chats = asyncio.run(Server.get_all_chats())
# print(chats[0].history)
if len(chats) == 0:
    asyncio.run(Server.create_chat("First Chat"))
    chats = asyncio.run(Server.chats)

# chat_names = []
# for chat in chats:
#     chat_names.append(chat._chat.name)

if "current_chat_id" not in st.session_state:
    st.session_state["current_chat_id"] = chats[0].id

current_chat = asyncio.run(Server.get_chat_by_id(st.session_state["current_chat_id"]))
st.title(current_chat.name)
container = st.container(border=True)

for message in current_chat.history:
    # print(message)
    container.chat_message(message["username"]).markdown(message["message"])


with st.sidebar:
    st.title("Chats")

    with st.expander("Chats", True):
        for chat in chats:
            st.button(chat.name, on_click=btn_click, kwargs={"index": chat.id})
    st.divider()
    with st.expander("Actions", True):
        want_upload = st.button("Upload Meeting")
        want_topic = st.button("Create Topic")


col1, col2 = st.columns([18, 100])

with col1:
    want_summary = st.button("Summary")

with col2:
    chat_input = st.chat_input("Ask a question about your meetings")

# React to user input
if chat_input:
    asyncio.run(current_chat.add_message("User", chat_input))
    container.chat_message("User").markdown(chat_input)
    asyncio.run(current_chat.add_message("Assistant", chat_input))
    container.chat_message("Assistant").markdown(chat_input)

if want_summary:
    st.switch_page("pages/summary.py")

if want_upload:
    st.switch_page("pages/upload_meeting.py")

if want_topic:
    st.switch_page("pages/create_topic.py")

