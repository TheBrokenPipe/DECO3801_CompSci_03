import streamlit as st
base_path = "pages/" 
file_list = [
    'chat.py',  # keep the default page first
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
page_list = []  # list of pages to be used to set up navigation

# pages: a Dictionary of pages to use when navigating
#   Key: name of page in /pages
#   Value: a st.Page object for the relevant page
pages = {}

for file in file_list:
    # Create a readable name by removing underscores and the file extension
    file_name = file.replace('.py', '')
    # Create the full path by concatenating base_path and file name
    full_path = base_path + file
    # Add to dictionary
    page = st.Page(full_path, title=file_name)
    page_list.append(page)
    pages[file_name] = page

pg = st.navigation(page_list, position="hidden")
pg.run()
