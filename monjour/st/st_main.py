import importlib
import os
from pathlib import Path

from monjour.app import App, DateRange
from monjour.st.st_app import get_st_app, StApp
from monjour.core.globals import MONJOUR_DEBUG

import streamlit as st

st_lib_home = Path(os.path.dirname(__file__))
# st.set_page_config(layout='wide')

######################################
# App setup
######################################

st.session_state.project_dir = os.path.curdir
st_app = get_st_app(st.session_state.project_dir)

# Will only run if the app is dirty
st_app.run()

######################################
# Pages
######################################

@st.cache_resource
def get_routes(_):
    if MONJOUR_DEBUG:
        debug_page = st.Page(st_lib_home / 'ui' / 'debug' / 'debug.py', title="Debug")
        jupyter_page = st.Page(st_lib_home / 'ui' / 'debug' / 'jupyter.py', title="Jupyter")

    GENERAL = st_lib_home / 'ui' / 'general'
    dash_page = st.Page(GENERAL / 'dash.py', title="Dashboard")
    archive_page = st.Page(GENERAL / 'archive.py', title="Archive")
    edit_page = st.Page(GENERAL / 'edit.py', title="Edit")

    REPORTS = st_lib_home / 'ui' / 'reports'
    income_expenses_page = st.Page(REPORTS / 'income_expenses.py', title="Income/Expenses")
    report_categories_page = st.Page(REPORTS / 'report_categories.py', title="By Categories")
    sankey_page = st.Page(REPORTS / 'sankey.py', title="Sankey")

    return (
        [debug_page, jupyter_page] if MONJOUR_DEBUG else [],
        [dash_page, archive_page, edit_page],
        [income_expenses_page, report_categories_page, sankey_page]
    )

debug, general, reports = get_routes(st.session_state.project_dir)

# User defined pages
user_pages = st_app.find_custom_st_pages()

######################################
# Layout that is shared between all pages
######################################

pg = st.navigation({
    **({} if len(debug) == 0 else { 'Debug': debug }),
    'GENERAL': general,
    'REPORTS': reports,
    **({} if len(user_pages) == 0 else { 'Custom Pages': user_pages })
})

pg.run()