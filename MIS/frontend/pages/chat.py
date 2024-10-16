import streamlit as st
import asyncio

from st_screen_stats import ScreenData
from MIS.frontend.interface import Server

print("Loading Chat")


chats = asyncio.run(Server.get_all_chats())

# chat_names = []
# for chat in chats:
#     chat_names.append(chat._chat.name)

if "current_chat_id" not in st.session_state:
    st.switch_page("pages/feed.py")
if "transcript_view_id" in st.session_state:
    st.switch_page("pages/transcript_view.py")

print(st.session_state["current_chat_id"])


def btn_click(index):
    st.session_state["current_chat_id"] = index


screenD = ScreenData(setTimeout=1500)
screen_d = screenD.st_screen_data()

current_chat = asyncio.run(
    Server.get_chat_by_id(st.session_state["current_chat_id"])
)
st.title(current_chat.name)
chat_container = st.container(border=True,
                              height=int(screen_d["innerHeight"] * 0.61))

for message in current_chat.history:
    # print(message)
    username = message["username"]
    text = message["message"]
    chat_container.chat_message(username).markdown(text)

chat_input = st.chat_input("Ask a question about your meetings")

latest_meetings = asyncio.run(Server.get_all_meetings())

with st.sidebar:
    home_button = st.button("Home", icon=":material/home:", key="home")

    with st.expander("Chats", True):
        new_chat_button = st.button("New Chat")
        summary_button = st.button("Chat Summary")
        st.divider()
        for chat in chats:
            if chat.id == st.session_state["current_chat_id"]:
                st.text(chat.name)
            else:
                st.button(chat.name, on_click=btn_click,
                          kwargs={"index": chat.id}, key="chat"+str(chat.id))

    with st.expander("Actions", True):
        upload_button = st.button("Upload Meeting", key="upload")
        new_topic_button = st.button("Create Topic", key="new_topic")


def source_btn_click(index):
    print("source_btn_click")
    st.session_state["transcript_view_id"] = index


source_buttons = []

# React to user input
if chat_input:
    chat_container.chat_message("User").markdown(chat_input)
    add_chat = asyncio.run(current_chat.add_message("User", chat_input))
    ai = "Assistant"
    waiting_message = chat_container.chat_message(ai).markdown("Lemme see...")
    response, sources = asyncio.run(current_chat.send_message(chat_input))

    asyncio.run(current_chat.add_message(ai, response))
    chat_container.chat_message(ai).markdown(response)
    chat_container.chat_message(ai).markdown(
        "Sources:\n" +
        "\n".join(list({source["meeting"].name for source in sources}))
    )
    if len(sources) > 0:
        columns = st.columns(min(5, len(sources)))  # button columns
        for index, source in enumerate(sources):
            with columns[index]:
                # hours, remainder = divmod(source["start_time"], 3600)
                # minutes, seconds = divmod(remainder, 60)
                # start_time = time(hour=int(hours), minute=int(minutes),
                #                   second=int(seconds))
                # + start_time.strftime("%H:%M:%S" if hours > 0 else "%M:%S")
                st.button(
                    source["meeting"].name + " " + (source["start_time"]),
                    on_click=source_btn_click,
                    kwargs={"index": source["meeting"].id}, key=source["key"]
                )

if home_button:
    del st.session_state["current_chat_id"]
    st.switch_page("pages/feed.py")

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
