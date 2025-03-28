# other imports
import streamlit as st
import datetime
from MIS.frontend.interface import server


def header():
    leftHeader, centreHeader, rightHeader = st.columns(3)
    leftHeader.button("Back")
    centreHeader.header("Logo")
    rightHeader.button("Help")


header()

topicHeader1, topicHeader2 = st.columns(2)
topicHeader1.write("Topic Name")
topicHeader2.write("Last Modified")

for topic in server.get_topics():
    topicContainer = st.container(border=True)
    topicContainer1, topicContainer2 = topicContainer.columns(2)
    topicContainer1.write(topic.get_name())
    topicContainer2.write(
        datetime.datetime.strftime(
            topic.get_modified_time(),
            "%d/%m/%y"
        )
    )
    topicContainer.button(key=topic.get_name(), label="edit")

st.button(key="createLabelButton", label="Create new Topic")
