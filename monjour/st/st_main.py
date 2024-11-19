import importlib
import os
from pathlib import Path

from monjour.app import App, DateRange
from monjour.st.st_app import StApp

import streamlit as st

st_lib_home = Path(os.path.dirname(__file__))

st.session_state.project_dir = os.path.curdir
st_app = StApp(st.session_state.project_dir)

######################################
# App setup
######################################

st_app.app.run()

######################################
# Pages
######################################

home_page = st.Page(st_lib_home / 'ui' / 'home.py', title="Home")
import_page = st.Page(st_lib_home / 'ui' / 'import.py', title="Import")
archive_page = st.Page(st_lib_home / 'ui' / 'archive.py', title="Archive")

# User defined pages
user_pages = st_app.find_custom_st_pages()

######################################
# Layout that is shared between all pages
######################################

pg = st.navigation({
    'General': [home_page],
    'Import': [import_page, archive_page],
    **({} if len(user_pages) == 0 else { 'Custom Pages': user_pages })
})

pg.run()