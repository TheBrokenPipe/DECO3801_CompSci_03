import streamlit as st
from index import pages

col1, col2 = st.columns([6, 1], gap="large", vertical_alignment="center")
with col1:
    if st.button('← Back', key="back"):
        st.switch_page(pages["upload_meeting2"])

# page content goes here

col1, col2, col3 = st.columns([1, 4, 1], gap="large", vertical_alignment="top")
with col1:
    if st.button("← Back", key="previous"):
        st.switch_page(pages["upload_meeting2"])

with col2:
    st.write("")

with col3:
    if st.button("Submit", key="submit"):
        st.switch_page(pages["chat"])