import streamlit as st

home_button = st.button("Home", icon=":material/home:", key="home")

if home_button:
    st.session_state["summarise_chat"] = True
    if "transcript_view_id" in st.session_state:
        del st.session_state["transcript_view_id"]
    if "current_chat_id" in st.session_state:
        del st.session_state["current_chat_id"]
    st.switch_page("pages/feed.py")

col1, col2 = st.columns([3, 1], gap="large", vertical_alignment="center")

with col1:
    col1_a, col1_b = st.columns([0.85, 1], vertical_alignment="center")

    with col1_a:
        st.title("Minutes in Seconds")

    with col1_b:
        st.subheader("| Help Center")

with col2:
    # contact_support_button = st.button("Contact Support")
    support = "Dial : ######### or Email : compsci_03@deco.com for support"
    with st.popover("Contact support"):
        st.markdown(support)


st.title("How can we help?")

search_faqs = st.text_input("Search our Frequently Asked Questions",
                            placeholder="Search...")


st. write("Search using key terms such as upload, transcript, and summary")

st.header("Frequently Asked Questions")

faqs_dict = [
    {"Q": "How do I interpret the summary provided?",
     "A": "Summaries highlight key points and main topics discussed during " +
          "the meeting. You can also view the full transcript for specifics."},
    {"Q": "What should I do if I encounter any issues?",
     "A": "If you face any issues, please contact our support team."},
    {"Q": "How do I upload an audio file for transcription?",
     "A": "You can attach your audio file on the upload page."},
    {"Q": "Is speech diarization available?",
     "A": "Not yet but we're working on it."},
    {"Q": "Are both the summary and full transcript of the meeting available",
     "A": "You can navigate to summaries via the chat page and access " +
          "transcripts on the transcript view page"},
]

filter_faqs_dict = [
    faq for faq in faqs_dict
    if search_faqs.lower() in faq['Q'].lower()
    or search_faqs.lower() in faq['A'].lower()
]

for faq in filter_faqs_dict:
    with st.expander(faq["Q"]):
        st.write(faq["A"])
