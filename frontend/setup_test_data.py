
async def setup_test_data1(server):
    topic = await server.create_topic("Executive Meetings", [])
    chat = await server.create_chat("Test CHat 1")
    return
    exec1 = server.upload_meeting(b'Hello World!', "meeting.txt", "First Executive Meeting", datetime.now(),
                                  updateSummary)
    exec2 = server.upload_meeting(b'Hello World!', "meeting.txt", "Second Executive Meeting", datetime.now(),
                                  updateSummary)
    topic.add_meeting(exec1)
    topic.add_meeting(exec2)
    topic2 = server.create_topic("Marketing Meetings", [], [user])
    mark1 = server.upload_meeting(b'Hello World!', "meeting.txt", "First Marketing Meeting", datetime.now(), [user],
                                  updateSummary)
    mark2 = server.upload_meeting(b'Hello World!', "meeting.txt", "Second Marketing Meeting", datetime.now(), [user],
                                  updateSummary)
    topic2.add_meeting(mark1)
    topic2.add_meeting(mark2)

    user.add_chat(chat)
    chat2 = Chat(user, [topic2])
    user.add_chat(chat2)

    chat.query(Message(chat.get_user(), "What's my name?"))
    chat.query(Message(chat.get_user(), "How are you?"))
    chat2.query(Message(chat.get_user(), "How much money did we get?"))
    chat2.query(Message(chat.get_user(), "When is self due?"))


