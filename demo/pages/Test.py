import streamlit as st

from monjour.st import get_st_app

st_app = get_st_app(st.session_state.project_dir)
df = st_app.app.df.copy()

st.title("Demo report")

st.dataframe(df.head(50))