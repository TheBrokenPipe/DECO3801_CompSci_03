from dotenv import load_dotenv
from manager import Thingo

load_dotenv()



t = Thingo(10)  # need a metadatafile
print("Transcribing:")
# t.add_audio_meeting_transcript_document("data/audio_recordings/en-US_AntiBERTa_for_word_boosting_testing.wav")
# t.add_to_db(t.embed_text("Pizza hut"))
# t.save_db()

transcription = t.asr.transcribe_audio_file("data/audio_recordings/en-US_AntiBERTa_for_word_boosting_testing.wav")
print(transcription)


# em = t.embed_text(transcription)

# print()
# print("Num embeddings saved: ", t.rag.vdb_index.ntotal)
# print()

print(t.query("What does the llm do?"))


exit()
exit()

for i in ["pizza is tasty", "chatgpt is an llm used to design proteins", "protein"]:
    print(t.query(i))
    # em = t.rag.embed_text(i)
    # print(t.rag.get_closest_indexes(em, 1))

# t.file_manager.save(t.rag.vdb_index, t.rag.link_db)

# ids = t.vdb_index.reconstruct_n(0, t.vdb_index.ntotal)
# print("All IDs:", ids)
# print(t.transcribe_audio_file("en-US_AntiBERTa_for_word_boosting_testing.wav"))

