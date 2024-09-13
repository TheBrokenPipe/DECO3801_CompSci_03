import streamlit as st
# Base path variable
base_path = "pages/"  # Change this to the actual path where the files are located
# File list extracted from the provided data
file_list = [
    'chat.py',
    'booting.py',
    'create_topic.py',
    'help.py',
    'summary.py',
    'topic_management.py',
    'transcript_view.py',
    'upload_meeting.py',
    'upload_meeting2.py'
]
# Create a list with pages
page_list = []
for file in file_list:
    # Create a readable name by removing underscores and the file extension
    readable_name = file.replace('.py', '')
    # Create the full path by concatenating base_path and file name
    full_path = base_path + file
    # Add to dictionary
    page_list.append(st.Page(full_path, title=readable_name))

pg = st.navigation(page_list, position="hidden")
pg.run()
