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
    chats = asyncio.run(Server.get_all_chats())

# chat_names = []
# for chat in chats:
#     chat_names.append(chat._chat.name)

if "current_chat_id" not in st.session_state:
    st.session_state["current_chat_id"] = asyncio.run(Server.get_latest_chats()).id

print(st.session_state["current_chat_id"])

current_chat = asyncio.run(Server.get_chat_by_id(st.session_state["current_chat_id"]))
st.title(current_chat.name)
container = st.container(border=True)

for message in current_chat.history:
    # print(message)
    container.chat_message(message["username"]).markdown(message["message"])

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


# col1, col2 = st.columns([18, 100])

#with col1:
#    summary_button = st.button("Summary")

#with col2:
chat_input = st.chat_input("Ask a question about your meetings")

# React to user input
if chat_input:
    asyncio.run(current_chat.add_message("User", chat_input))
    container.chat_message("User").markdown(chat_input)
    asyncio.run(current_chat.add_message("Assistant", chat_input))
    container.chat_message("Assistant").markdown(chat_input)

if new_chat_button:
    st.switch_page("pages/create_chat.py")

if summary_button:
    st.switch_page("pages/summary.py")

if upload_button:
    st.switch_page("pages/upload_meeting.py")

if new_topic_button:
    st.switch_page("pages/create_topic.py")

