import datetime
import random
import streamlit as st


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
    return datetime.datetime(2024, 1, 1)


leftHeader, centreHeader, rightHeader = st.columns(3)
header_back = leftHeader.button("Back", key="fsdwe")
centreHeader.header("Logo")
header_help = rightHeader.button("Help", key="idjwn")

if header_back:
    st.switch_page("pages/chat.py")

if header_help:
    st.switch_page("pages/help.py")

date_string = datetime.datetime.strftime(get_meeting_date(), "%d/%m/%Y")
st.header(f"{get_meeting_name()} ({date_string})")

# a list of all (speaker, texts) for this transcript
paras = zip(get_para_speaker_names(), get_para_texts())

for (speaker, text) in paras:
    speaker_char = speaker[-1]  # unique char to represent the speaker
    st.chat_message(speaker_char).markdown(speaker + ": " + text)