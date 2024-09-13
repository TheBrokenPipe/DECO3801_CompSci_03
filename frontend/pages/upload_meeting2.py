import streamlit as st

col1, col2 = st.columns([6, 1], gap = "large", vertical_alignment="center")
with col1:
    st.button('← Back')

with col2:
    st.button('Help')

st.write('Are there any text documents that are important context for this meeting? Please upload them here')

uploaded_file = st.file_uploader("Upload supporting documents", type=['txt'])
