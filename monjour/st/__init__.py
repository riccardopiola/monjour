import sys
import os
import streamlit.web.cli as stcli
import streamlit as st

def st_main():
    app_entry_file = os.path.join( os.path.dirname(__file__), 'st_main.py')
    sys.argv = ["streamlit", "run", app_entry_file]

    # This will start the server on this thread and
    # run the streamlit script on a different thread
    stcli.main()

from monjour.st.st_app import StApp
