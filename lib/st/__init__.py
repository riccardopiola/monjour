import sys
import os
import streamlit.web.cli as stcli

def st_main():
    app_entry_file = os.path.join( os.path.dirname(__file__), 'app.py')
    sys.argv = ["streamlit", "run", app_entry_file]

    # os.chdir()

    # This will start the server on this thread and
    # run the streamlit script on a different thread
    stcli.main()