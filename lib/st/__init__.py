import sys
import os
import streamlit.web.cli as stcli

def st_main():
    app_entry_file = os.path.join( os.path.dirname(__file__), 'st_home.py')
    sys.argv = ["streamlit", "run", app_entry_file]

    # This will start the server on this thread and
    # run the streamlit script on a different thread
    stcli.main()