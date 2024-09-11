col1, col2 = st.columns([3, 1], gap = "large", vertical_alignment="center")

with col1:
     col1_a, col1_b = st.columns([0.85, 1], vertical_alignment="center")
     

     with col1_a:
          st.title("AppName")

     with col1_b:
         st.subheader("| Help Center")

with col2:
      st.button("Contact Support")

st.title("How can we help?")

search_bar = st.text_input("", placeholder="Search...")
