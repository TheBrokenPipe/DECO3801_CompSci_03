import streamlit as st
from interface import *

def btn_click(index):
    st.session_state["current_chat"] = index

def upload_meeting():
    # dummy
    i = 5

user = server.get_user("user")
if user is None:
    user = server.create_user("user", "p@ssword")

chats = user.get_chats()

chat_names = []
for chat in chats:
    chat_names.append(chat.get_topics()[0].get_name())

if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = 0

with st.sidebar:
    st.title("Chats")

    with st.expander("Chats", True):
        for i in range(len(chat_names)):
            st.sidebar.button(chat_names[i], on_click=btn_click, args=[i])
    st.divider()
    with st.expander("Actions", True):
        st.sidebar.button("Upload meeting", on_click=upload_meeting)

st.title(chat_names[st.session_state["current_chat"]])

# constants
CHAT_PROMPT = "Ask a question about your meetings"  # TODO: confirm with group

for message in chats[st.session_state["current_chat"]].get_messages():
    with st.chat_message(message.get_sender().get_name()):
        st.markdown(message.get_text())

col1, col2 = st.columns([18,100]) 

chat_input = None
want_summary = None
with col1:
    want_summary = st.button("Summary")

with col2:
    chat_input = st.chat_input(CHAT_PROMPT)

# React to user input
if chat_input:
    msg = Message(chats[st.session_state["current_chat"]].get_user(), chat_input)
    st.chat_message(msg.get_sender().get_name()).markdown(msg.get_text())
    resp = chats[st.session_state["current_chat"]].query(msg)
    st.chat_message(resp.get_sender().get_name()).markdown(resp.get_text())

if want_summary:
    st.switch_page(st.Page("pages/summary.py", title="summary"))