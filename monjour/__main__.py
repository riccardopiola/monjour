import argparse
import sys
import os

import monjour.core.log as log
from monjour.core.globals import MONJOUR_DEBUG, MONJOUR_LOG_LEVEL

parser = argparse.ArgumentParser()
parser.add_argument('--init', action='store_true', help='Initialize a project in the current directory')
parser.add_argument('--demo', type=str, help='Run the demo')
parser.add_argument('-st', '--streamlit', action='store_true', help='Run the Streamlit server')
parser.add_argument('--console', action='store_true', help='Launch the separate admin console')
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
parser.add_argument('--log_level', type=str, help='Set the log level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
parser.add_argument('project', nargs=1, help='Project directory')
args = parser.parse_args()

if args.debug:
    MONJOUR_DEBUG = 'True'
    os.environ['MONJOUR_DEBUG'] = MONJOUR_DEBUG

if args.log_level:
    MONJOUR_LOG_LEVEL = args.log_level
    os.environ['MONJOUR_LOG_LEVEL'] = MONJOUR_LOG_LEVEL


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