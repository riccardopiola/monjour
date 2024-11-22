import importlib
import os
from pathlib import Path

from monjour.app import App, DateRange
from monjour.st.st_app import get_st_app

import streamlit as st

st_lib_home = Path(os.path.dirname(__file__))
st.set_page_config(layout='wide')

st.session_state.project_dir = os.path.curdir
st_app = get_st_app(st.session_state.project_dir)

######################################
# App setup
######################################

st_app.app.run()

######################################
# Pages
######################################

debug_page = st.Page(st_lib_home / 'ui' / 'debug.py', title="Debug")

home_page = st.Page(st_lib_home / 'ui' / 'home.py', title="Home")
import_page = st.Page(st_lib_home / 'ui' / 'import.py', title="Import")
archive_page = st.Page(st_lib_home / 'ui' / 'archive.py', title="Archive")

# User defined pages
user_pages = st_app.find_custom_st_pages()

######################################
# Layout that is shared between all pages
######################################

pg = st.navigation({
    # **({} if len(user_pages) == 0 else { 'Debug': user_pages })
    'Debug': [ debug_page],
    'General': [home_page, import_page, archive_page],
    **({} if len(user_pages) == 0 else { 'Custom Pages': user_pages })
})

pg.run()