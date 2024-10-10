from datetime import datetime
import random
import streamlit as st
from interface import Server
import asyncio, json


if "transcript_view_id" not in st.session_state:
    st.switch_page("pages/chat.py")
    # st.session_state["transcript_view_id"] = -1


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


leftHeader, centreHeader, rightHeader = st.columns(3)
header_back = leftHeader.button("Back", key="fsdwe")
centreHeader.header("Logo")
header_help = rightHeader.button("Help", key="idjwn")

if header_back:
    st.switch_page("pages/chat.py")

if header_help:
    st.switch_page("pages/help.py")

meeting = asyncio.run(Server.get_meeting_by_id(st.session_state["transcript_view_id"]))

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
            st.markdown(
                f'''
                :{speaker_colors[speaker]}[{speaker}]: {line['text']}
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
