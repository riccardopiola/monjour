import sys
import streamlit.cli as stcli

import lib.st.app as app

def st_main():
    sys.argv = ["streamlit", "run", "app.py"]

    # Use Streamlit's internal command line interface to run the app
    stcli._main_run_clauses = (app, )
    stcli.main()