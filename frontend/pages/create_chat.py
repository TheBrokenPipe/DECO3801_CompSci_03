import streamlit as st
from interface import Server
import streamlit_tags as stt
import asyncio

col1, col2 = st.columns([6, 1], gap="large", vertical_alignment="center")
with col1:
    if st.button('← Back'):
        st.switch_page("pages/chat.py")

with col2:
    if st.button('Help'):
        st.switch_page("pages/help.py")

topics = asyncio.run(Server.get_all_chats())

with st.expander("Current Chat"):
    for topic in topics:
        st.write(topic.name)

st.title("Create New Chat")

meeting_name = st.text_input("New Chat name:")

existing_topics = asyncio.run(Server.get_all_topics())

selected_topics = stt.st_tags(
    label='Existing Topics',
    text='Press enter to add more',
    value=[],
    suggestions=[t.name for t in existing_topics],
    key="hello"
)

want_create = st.button("Create")

if want_create:
    selected_topics = [st.lower() for st in selected_topics]

    asyncio.run(
        Server.create_chat(
            meeting_name,
            [t for t in existing_topics if t.name.lower() in selected_topics]
        )
    )

    st.switch_page("pages/chat.py")
