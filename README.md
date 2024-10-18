# Minutes In Seconds (MIS)
A web application where users can upload meetings and meeting-like events, which are transcribed and summarised. Then, users can query within or across the context of all the meetings.

**Please note that a full installation from scratch will need 5 to 20+ GB of free disk space depending on model specifics and GPU acceleration.**

## Installation
1. Install Python 3 from [here](https://www.python.org/downloads/)
2. Install pytorch per instructions [here](https://pytorch.org/get-started/locally/)
3. Install remaining python dependencies by running `pip install -r requirements.txt`
4. Install Ollama from [here](https://ollama.com/download)
5. Install FFmpeg from [here](https://ffmpeg.org/download.html)
6. Install Docker from [here](https://www.docker.com/)

## Setup
Make sure Docker is running, then run `python setup.py` and follow the prompts.

## Usage
"Minutes in Seconds" is split into frontend and backend components. Start by making sure Docker is running, then run the relevant commands below to start each component:
   *  Frontend - `python -m streamlit run MIS/frontend/index.py`
   *  Backend - `python main.py`

## Production Dependencies
### Platforms / Tools
[Python 3](https://www.python.org/) | [Docker](https://www.docker.com/) | [pgvector](https://hub.docker.com/r/pgvector/pgvector) | [Ollama](https://ollama.com/) | [FFmpeg](https://ffmpeg.org)

### Libraries
[langchain](https://github.com/langchain-ai/langchain) | [langchain_community](https://pypi.org/project/langchain-community/) | [langchain_postgres](https://pypi.org/project/langchain-postgres/) | [langchain_openai](https://pypi.org/project/langchain-openai/) | [Streamlit](https://github.com/streamlit/streamlit) | [Streamlit-tags](https://pypi.org/project/streamlit-tags/) | [docker](https://pypi.org/project/docker/) | [psycopg](https://pypi.org/project/psycopg/) | [python-dotenv](https://pypi.org/project/python-dotenv/) | [requests](https://pypi.org/project/requests/) | [WhisperX](https://github.com/Hasan-Naseer/whisperX/) | [langchain-ollama](https://pypi.org/project/langchain-ollama/)

### AI Models
* [Systran / Distil-Whisper: faster-distil-whisper-large-v3](https://huggingface.co/Systran/faster-distil-whisper-large-v3) - ASR
* [OpenAI: GPT-4o-mini](https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/) - LLM FM
* [OpenAI: text-embedding-3-large](https://openai.com/index/new-embedding-models-and-api-updates/) - RAG embedding
* [Ollama / Nomic: nomic-embed-text v1.5](https://ollama.com/library/nomic-embed-text:v1.5) - semantic chunking embedding


## Data Sources
* [AMI Corpus](https://groups.inf.ed.ac.uk/ami/corpus/) - source of meeting recordings for test and sample data, used under Creative Commons open licence

## Test Dependencies
### AI Models
* [Ollama / Meta: llama3.1:8b-instruct-q4_0](https://ollama.com/library/llama3.1:8b-instruct-q4_0) - LLM FM
* [Ollama / Meta: llama3.2:3b-instruct-q4_K_M ](https://ollama.com/library/llama3.2:3b-instruct-q4_K_M) - LLM FM
