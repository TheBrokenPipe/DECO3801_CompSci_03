
import streamlit as st
import streamlit_tags as stt
from MIS.frontend.interface import Server
import asyncio

want_back = None

col1, col2 = st.columns([6, 1], gap="large", vertical_alignment="center")
with col1:
    want_back = st.button('← Back')

with col2:
    if st.button('Help'):
        st.switch_page("pages/help.py")

st.write('Welcome! To start uploading your meeting, please give the meeting a unique name and upload the transcript/recording from your computer')

meeting_name = st.text_input("Enter the name of the meeting:")

meeting_date = st.date_input("On what date did the event take place?", format="DD/MM/YYYY")

existing_topics = asyncio.run(Server.get_all_topics())
selected_topics = stt.st_tags(
    label='Existing Topics',
    text='Press enter to add more',
    value=[],
    suggestions=[t.name for t in existing_topics],
    key="hello"
)
selected_topics = [st.lower() for st in selected_topics]
print(selected_topics)
print([t for t in existing_topics if t.name.lower() in selected_topics])


uploaded_file = st.file_uploader("Upload Recording/Transcript", type=['mp3', 'mp4', 'txt', 'wav'])

if uploaded_file is not None:
    st.write(f"{meeting_name} uploaded successfully.")

col1, col2 = st.columns([6.5, 1], gap="large", vertical_alignment="top")
with col1:
    st.write("")

with col2:
    next1 = st.button("Next", key="NextFromUpload1")

if next1:
    asyncio.run(
        Server.upload_meeting(
            name=meeting_name,
            date=meeting_date,
            file=uploaded_file,
            topics=[t for t in existing_topics if t.name.lower() in selected_topics]
        )
    )
    if "current_chat_id" not in st.session_state:
        st.switch_page("pages/feed.py")
    else:
        st.switch_page("pages/chat.py")

    # TODO skipping the rest to make this work
    if uploaded_file:
        st.session_state["new_meeting_name"] = meeting_name
        st.session_state["new_meeting_date"] = meeting_date
        st.session_state["new_meeting_file"] = uploaded_file
        st.switch_page("pages/upload_meeting2.py")
    else:
        st.warning("Please upload a main meeting file")

# if st.button("Next", key = "next_buttonB"):
#         st.session_state.page = "upload_page2"

# if st.session_state.page == "upload_page1":
#     upload_page1()

if want_back:
    if "current_chat_id" not in st.session_state:
        st.switch_page("pages/feed.py")
    else:
        st.switch_page("pages/chat.py")