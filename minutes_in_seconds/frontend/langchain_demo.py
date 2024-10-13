import streamlit as st
from langchain_openai.chat_models import ChatOpenAI

# source: https://docs.streamlit.io/develop/tutorials/llms/llm-quickstart

st.title("🦜🔗 Quickstart App")

openai_api_key = ""  # TODO: get from Rick


def generate_response(input_text):
    model = ChatOpenAI(temperature=0.7, api_key=openai_api_key)
    st.info(model.invoke(input_text))


with st.form("my_form"):  # TODO: replace this with chat_input
    text = st.text_area(
        "Enter text:",
        "What are the three key pieces of advice for learning how to code?",
    )
    submitted = st.form_submit_button("Submit")
    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    if submitted and openai_api_key.startswith("sk-"):
        generate_response(text)