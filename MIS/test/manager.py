def upload_file_from_streamlit(self, uploaded_file: streamFile):
    time_tag = datetime.now().timestamp()
    audio_file_path = f"audio_recordings/audio_uploaded_{time_tag}.wav"

    # Open a file in write-binary mode and write the contents of the uploaded file to it
    with open(audio_file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer().tobytes())

    print(f"File saved to {audio_file_path}")
    """from uploaded file"""
    # Save the uploaded file to a temporary file
    # print(uploaded_file.read())
    # return 1
    # with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
    #     tmp_file.write(uploaded_file.read())
    #     tmp_file_path = tmp_file.name
    transcription = self.asr.transcribe_audio(uploaded_file)
    # self.rag.extract_objects(transcription)
    # exit()
    summary = self.rag.summarise_meeting(transcription)['abstract_summary']  # TODO just using the abstract for now
    save_transcript_file_path = self.file_manager.save_text_file(summary)
    self.rag.add_document(summary, save_transcript_file_path)
    self.file_manager.save(self.rag.vdb_index, self.rag.link_db)


def add_audio_meeting_transcript_document(self, file_path: str):

    """from path"""
    # assert False  # TODO save transcript as a txt file
    transcription = self.asr.transcribe_audio_file(file_path)
    summary = self.rag.summarise_meeting(transcription)['abstract_summary']  # TODO just using the abstract for now
    save_transcript_file_path = self.file_manager.save_text_file(summary)
    self.rag.add_document(summary, save_transcript_file_path)
    self.file_manager.save(self.rag.vdb_index, self.rag.link_db)


def add_text_document(self, file_path: str):
    """from path"""
    with open(file_path, "r") as file:
        text = str(file.read())
    summary = self.rag.summarise_meeting(text)
    print(summary)
    return summary
    self.rag.add_document(text, file_path)
    self.file_manager.save(self.rag.vdb_index, self.rag.link_db)


def query(self, query_text: str):
    return self.rag.query(query_text)
