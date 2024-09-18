import streamlit as st
import time
from index import pages


def header():
    leftHeader, centreHeader, rightHeader = st.columns(3)
    leftHeader.button("Back")
    centreHeader.header("Logo")
    rightHeader.button("Help")


header()

with st.spinner("Loading application"):
    # load everything needed here.
    time.sleep(1)

st.switch_page(pages["chat"])
