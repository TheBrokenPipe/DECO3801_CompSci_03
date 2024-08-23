# CompSci_03
## project structure and descriptions of file
```
|- frontend  ( a folder for code relating to the front end )
|----- index.py           <- a prototype of the UI to integrate with any early work on the backend
|----- langchain_demo.py  <- a tutorial using streamlit and langchain with minor modifications
|- ASR.py            <- backend code for automated speech recognition
|- RAG.py            <- backend code for retrieval augmented generation
|- main.py           <- backend code for running the main
|- requirements.txt  <- the list of requirements/dependencies for this project
```

## Information on the tools we use
## Streamlit
we are trialing streamlit for frontend/frontend prototyping

#### how to use streamlit?
streamlit run your_script.py
[Main Streamlit concepts](https://docs.streamlit.io/get-started/fundamentals/main-concepts)

### Langchain
Langchain can help us coordinate and implement tools in our data pipeline
=======
## Dependencies
* [Python 3](https://www.python.org/)
* [Faiss](https://github.com/facebookresearch/faiss)
* [OpenAI](https://github.com/openai/openai-python)
* [bidict](https://github.com/jab/bidict)
* [NumPy](https://github.com/numpy/numpy)
* [Langchain](https://github.com/langchain-ai/langchain)
* [Streamlit](https://github.com/streamlit/streamlit)

## Installation and Usage
1. Install Python 3 (minimum Python version 3.11)
2. Install install dependencies by running `pip install -r requirements.txt`
3. Start the project by
   *  Frontend prototype - `streamlit run index.py`
   *  Backend prototype - `python main.py`

