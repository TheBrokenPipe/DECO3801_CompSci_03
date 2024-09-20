import streamlit as st
from interface import *
from index import pages

print("Loading Chat")

def btn_click(index):
    st.session_state["current_chat"] = index
print(1)
user = server.get_user("user")
if user is None:
    user = server.create_user("user", "p@ssword")

print(2)
chats = user.get_chats()
print(3)

chat_names = []
for chat in chats:
    chat_names.append(chat.get_topics()[0].get_name())
print(4)

if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = 0
print(5)

want_upload = None
want_topic = None
# st.button("testBUTN", key=f"Test")

with st.sidebar:
    st.title("Chats")

    with st.expander("Chats", True):
        print("Setting Chats")
        for i, chat_name in enumerate(chat_names):
            # create a button that will change the current chat to the ith chat
            st.button(chat_name, on_click=btn_click, kwargs={"index": i})
    st.divider()
    with st.expander("Actions", True):
        want_upload = st.button("Upload Meeting")
        want_topic = st.button("Create Topic")

st.title(chat_names[st.session_state["current_chat"]])

# constants
CHAT_PROMPT = "Ask a question about your meetings"  # TODO: confirm with group

container = st.container(border=True, height=300)

for message in chats[st.session_state["current_chat"]].get_messages():
    container.chat_message(message.get_sender().get_name()).markdown(message.get_text())

col1, col2 = st.columns([18, 100])

chat_input = None
want_summary = None

with col1:
    want_summary = st.button("Summary")

with col2:
    chat_input = st.chat_input(CHAT_PROMPT)

# React to user input
if chat_input:
    msg = Message(chats[st.session_state["current_chat"]].get_user(), chat_input)
    container.chat_message(msg.get_sender().get_name()).markdown(msg.get_text())
    resp = chats[st.session_state["current_chat"]].query(msg)
    container.chat_message(resp.get_sender().get_name()).markdown(resp.get_text())

if want_summary:
    st.switch_page(pages["summary"])

if want_upload:
    st.switch_page(pages["upload_meeting"])

if want_topic:
    st.switch_page(pages["create_topic"])

