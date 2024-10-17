from datetime import datetime, time
import streamlit as st
from MIS.frontend.interface import Server
import asyncio
import json


if "transcript_view_id" not in st.session_state:
    print("transcript failed to show")
    st.switch_page("feed.py")


# return ordered array of the text paragraphs for the transcript
def get_para_texts():
    return ["Hello"] * 6


# return ordered array of all the speakers to allign with the paragraphs
def get_para_speaker_names():
    return ['Speaker 1', 'Speaker 2', 'Speaker 3', 'Speaker 4', 'Speaker 5',
            'Speaker 6']


def get_meeting_name():
    return "Meeting name"


def get_meeting_date():
    return datetime(2024, 1, 1)


st.markdown(
    """
    <style>
    .centered-header {
        text-align: center;
        margin: 0 auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

leftHeader, centreHeader, rightHeader = st.columns([1, 5, 1],
                                                   vertical_alignment="center")

header_back = leftHeader.button("Back", key="fsdwe")
with centreHeader:
    st.markdown('<h2 class="centered-header">Transcript</h2>',
                unsafe_allow_html=True)
header_help = rightHeader.button("Help", key="idjwn")

if header_back:
    del st.session_state["transcript_view_id"]
    if not st.session_state["summarise_chat"]:
        st.switch_page("summary.py")
    elif "current_chat_id" in st.session_state:
        st.switch_page("chat.py")
    else:
        st.switch_page("feed.py")

if header_help:
    st.switch_page("help.py")

meeting = asyncio.run(
    Server.get_meeting_by_id(st.session_state["transcript_view_id"])
)


def colors():
    colors = ["red", "blue", "green", "violet", "orange"]
    c_i = 0
    while True:
        yield colors[c_i]
        c_i += 1
        if c_i == len(colors):
            c_i = 0


speaker_colors = {}
colorgen = colors()

if meeting.transcript:
    with open(meeting.transcript) as f:
        for line in f.readlines():
            line = json.loads(line)
            speaker = line['speaker']
            if speaker not in speaker_colors:
                speaker_colors[speaker] = colorgen.__next__()
            start_time = line['start_time']
            hours, remainder = divmod(start_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            start_time = time(hour=int(hours), minute=int(minutes),
                              second=int(seconds))

            start_time = start_time.strftime("%H:%M:%S" if hours > 0
                                             else "%M:%S")

            timestamp = f"{speaker_colors[speaker]}[{start_time}]"
            text = line['text']
            st.markdown(
                f'''
                :{timestamp} - :{speaker_colors[speaker]}[{speaker}]: {text}
                '''
            )
else:
    st.text(f"No filepath for this meeting: {meeting.name}")

# date_string = datetime.strftime(get_meeting_date(), "%d/%m/%Y")
# st.header(f"{get_meeting_name()} ({date_string})")
#
# # a list of all (speaker, texts) for this transcript
# paras = zip(get_para_speaker_names(), get_para_texts())
#
# for (speaker, text) in paras:
#     speaker_char = speaker[-1]  # unique char to represent the speaker
#     st.chat_message(speaker_char).markdown(speaker + ": " + text)
