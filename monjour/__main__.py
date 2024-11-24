import argparse
import sys
import os

import monjour.core.log as log

parser = argparse.ArgumentParser()
parser.add_argument('--init', action='store_true', help='Initialize a project in the current directory')
parser.add_argument('--demo', type=str, help='Run the demo')
parser.add_argument('-st', '--streamlit', action='store_true', help='Run the Streamlit server')
parser.add_argument('--console', action='store_true', help='Launch the separate admin console')
parser.add_argument('project', nargs=1, help='Project directory')
args = parser.parse_args()

proj_dir = os.path.realpath(args.project[0])
if not os.path.isdir(proj_dir):
    print(f"Error: Project directory '{proj_dir}' does not exist")
os.environ['MONJOUR_ORIGINAL_CWD'] = os.getcwd()
os.environ['MONJOUR_PROJECT_DIR'] = proj_dir
os.chdir(proj_dir)
log.info(f"Changed working directory to {os.getcwd()}")
sys.path.append(proj_dir)

if args.streamlit:
    import streamlit.web.cli as stcli
    import streamlit as st

    app_entry_file = os.path.join( os.path.dirname(__file__), 'st', 'st_main.py')
    sys.argv = ["streamlit", "run", app_entry_file]

    # This will start the server on this thread and
    # run the streamlit script on a different thread
    stcli.main()