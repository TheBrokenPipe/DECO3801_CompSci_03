import json

from dotenv import load_dotenv
from manager import Thingo
from docker_manager import DockerManager
from database_manager import DB_Manager

load_dotenv()


# with PG_Manager(remove_when_done=False) as m:
#     m.full_setup()
#     DB_Manager.full_setup()
t = Thingo(10, pg_manager=1)  # need a metadatafile
data = []
with open("data/saved_docs/ES2016a_transcript.txt", "r") as f:
    for line in f:
        data.append(json.loads(line))
print(t.rag.identify_speakers(data))


# print(data)
    # exit()

    # print(t.rag.identify_speakers(data))
    # t.add_text_document("data/saved_docs/ES2016a_transcript.txt")

exit()
# with open("data/saved_docs/file_test.txt", 'r') as f:
#     t.rag.extract_objects(f.read())
# exit()


print("Transcribing:")
# t.add_audio_meeting_transcript_document("data/audio_recordings/en-US_AntiBERTa_for_word_boosting_testing.wav")
# t.add_to_db(t.embed_text("Pizza hut"))
# t.save_db()

transcription = t.asr.transcribe_audio_file("data/audio_recordings/legal.mp3")
print(transcription)
print()

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

{
    'abstract_summary': "In a project meeting led by Nick DeBusk, the team discusses the development of a new, "
                        "innovative remote control. Each member introduces their roles: Corinne Whiting as the "
                        "marketing expert, Ryan as the user interface designer, and Manuel as the industrial designer. "
                        "They outline the design phases—functional, conceptual, and detailed—and brainstorm ideas for "
                        "the remote's features, emphasizing the need for it to be trendy, user-friendly, and universal. "
                        "Suggestions include a tracking device to prevent loss, a spherical shape for stability, "
                        "and ergonomic designs for ease of use. The team acknowledges the challenges of balancing "
                        "aesthetics with functionality and stability, ultimately deciding to explore a design that "
                        "incorporates grips for better handling while maintaining a modern look. "
                        "The meeting concludes with plans for further research into market preferences and a follow-up "
                        "discussion on design concepts.",
    'key_points': {'key_points': [
        {'text': 'Introduction of the project and roles of team members'},
        {'text': 'Creating a new type of remote control that is original, trendy, and easy to use.'},
        {'text': 'Conceptual phases outlined: functional design, conceptual design, and detailed design.'},
        {'text': 'Discussion on universal functionality and market appeal for different target audiences.'},
        {'text': 'Idea generation around a design that is modern, sturdy, and easy to find.'},
        {'text': 'Exploration of various design shapes including ball, keyboard type, and grip considerations.'},
        {'text': 'Consideration of materials, sturdiness, and user-friendliness in design.'},
        {'text': 'Emphasis on the importance of a unique design that stands out from traditional remotes.'},
        {'text': 'Finalizing on an appropriate design plan and gathering feedback for the next meeting.'}
    ]},
    'action_items': {
        'action_items': [
            {
                'text': 'Conduct research on user requirements specification for the remote control project.',
                'assigned_people_names': ['Corinne Whiting'],
                'due_date': '2023-11-01'
            }, {
                'text': 'Perform trend watching for the remote control project during the conceptual design phase.',
                'assigned_people_names': ['Corinne Whiting'],
                'due_date': '2023-11-01'
            }, {
                'text': 'Conduct marketing research on the web regarding trends in remote controls.',
                'assigned_people_names': ['Corinne Whiting'],
                'due_date': '2023-11-01'
            }, {
                'text': 'Evaluate product requirements and rank them in the detailed design phase.',
                'assigned_people_names': ['Corinne Whiting'],
                'due_date': '2023-11-01'
            }, {
                'text': 'Investigate technical functions of the remote control for the functional design phase.',
                'assigned_people_names': ['Ryan'],
                'due_date': '2023-11-01'},
            {
                'text': 'Design user interface interactions for the conceptual design phase.',
                'assigned_people_names': ['Ryan'],
                'due_date': '2023-11-01'
            }, {
                'text': 'Determine design aspects regarding user preferences in the detailed design phase.',
                'assigned_people_names': ['Ryan'],
                'due_date': '2023-11-01'
            }, {
                'text': 'Discuss and finalize functional design requirements for the remote control.',
                'assigned_people_names': ['Manuel'],
                'due_date': '2023-11-01'
            }, {
                'text': 'Evaluate properties and materials for the conceptual design of the remote control.',
                'assigned_people_names': ['Manuel'],
                'due_date': '2023-11-01'
            }, {
                'text': 'Attend and contribute to the next design meeting with initial concepts for the remote control.',
                'assigned_people_names': ['Nick DeBusk', 'Corinne Whiting', 'Ryan', 'Manuel'],
                'due_date': '2023-11-15'
            }, {
                'text': 'Conduct a marketing analysis to identify universally appealing remote control designs.',
                'assigned_people_names': ['Corinne Whiting'],
                'due_date': '2023-11-15'
            }
        ]
    }
}
