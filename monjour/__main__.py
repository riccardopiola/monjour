import argparse
import sys
import os

parser = argparse.ArgumentParser()
parser.add_argument('--init', action='store_true', help='Initialize a project in the current directory')
parser.add_argument('--demo', type=str, help='Run the demo')
parser.add_argument('-st', '--streamlit', action='store_true', help='Run the Streamlit server')
parser.add_argument('--console', action='store_true', help='Launch the separate admin console')
args = parser.parse_args()

if args.streamlit:
    import streamlit.web.cli as stcli
    import streamlit as st

    app_entry_file = os.path.join( os.path.dirname(__file__), 'st_main.py')
    sys.argv = ["streamlit", "run", app_entry_file]

    # This will start the server on this thread and
    # run the streamlit script on a different thread
    stcli.main()