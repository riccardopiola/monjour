import streamlit as st

from monjour.st import get_st_app

st_app = get_st_app(st.session_state.project_dir)

st_app.app