import streamlit as st
from index import pages

col1, col2 = st.columns([6, 1], gap = "large", vertical_alignment="center")
with col1:
    if st.button('← Back'):
        st.switch_page(pages["upload_meeting"])

with col2:
    if st.button('Help'):
        st.switch_page(pages["help"])

st.write('Are there any text documents that are important context for this meeting? Please upload them here')

uploaded_file = st.file_uploader("Upload supporting documents", type=['txt'])
