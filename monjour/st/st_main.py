import importlib
import os
from pathlib import Path

from monjour.app import App, DateRange
from monjour.st.st_app import get_st_app
from monjour.core.globals import MONJOUR_DEBUG

import streamlit as st

st_lib_home = Path(os.path.dirname(__file__))
# st.set_page_config(layout='wide')

######################################
# App setup
######################################

st.session_state.project_dir = os.path.curdir
st_app = get_st_app(st.session_state.project_dir)

if not st_app.has_run:
    st_app.run()

######################################
# Pages
######################################

if MONJOUR_DEBUG:
    debug_page = st.Page(st_lib_home / 'ui' / 'debug' / 'debug.py', title="Debug")
    jupyter_page = st.Page(st_lib_home / 'ui' / 'debug' / 'jupyter.py', title="Jupyter")

GENERAL = st_lib_home / 'ui' / 'general'
dash_page = st.Page(GENERAL / 'dash.py', title="Home")
import_page = st.Page(GENERAL / 'import.py', title="Import")
archive_page = st.Page(GENERAL / 'archive.py', title="Archive")
edit_page = st.Page(GENERAL / 'edit.py', title="Edit")

REPORTS = st_lib_home / 'ui' / 'reports'
test_page = st.Page(REPORTS / 'report.py', title="Test")

# User defined pages
user_pages = st_app.find_custom_st_pages()

######################################
# Layout that is shared between all pages
######################################

pg = st.navigation({
    **({} if not MONJOUR_DEBUG else { 'Debug': [debug_page, jupyter_page] }),
    'General': [dash_page, import_page, archive_page, edit_page],
    'Reports': [test_page],
    **({} if len(user_pages) == 0 else { 'Custom Pages': user_pages })
})

pg.run()