import streamlit as st

col1, col2 = st.columns([6, 1], gap = "large", vertical_alignment="center")
with col1:
    if st.button('← Back', key="back2upload1"):
        st.switch_page("pages/upload_meeting.py")

with col2:
    if st.button('Help'):
        st.switch_page("pages/help.py")

st.write('Are there any text documents that are important context for this meeting? Please upload them here')

uploaded_file = st.file_uploader("Upload supporting documents", type=['txt'])

col1, col2, col3 = st.columns([1.5, 4, 1], gap="large", vertical_alignment="top")
with col1:
    if st.button("Previous", key="previous"):
        st.switch_page("pages/upload_meeting.py")

with col2:
    st.write("")

with col3:
    if st.button("Next"):
        st.session_state["new_meeting_supporting_file"] = uploaded_file
        st.switch_page("pages/upload_meeting3.py")

