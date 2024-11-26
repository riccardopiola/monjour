import argparse
import sys
import os
import json
import importlib.resources as resources

import monjour.core.log as log
from monjour.core.globals import MONJOUR_DEBUG, MONJOUR_LOG_LEVEL

parser = argparse.ArgumentParser()
# parser.add_argument('--init', action='store_true', help='Initialize a project in the current directory')
parser.add_argument('--console', action='store_true', help='Launch the separate admin console')
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
parser.add_argument('--log_level', type=str, help='Set the log level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
parser.add_argument('-st', '--streamlit', action='store_true', help='Run the Streamlit server')
parser.add_argument('-Xstreamlit', action='append', nargs='*', help='Any argument that will be passed to streamlit (exampple -Xstreamlit server.port 8501)')
parser.add_argument('-Xapp', action='append', nargs='*', help='Arguments of type key=value to pass to the app')
parser.add_argument('--demo', action='store_true', help='Run the demo')

parser.add_argument('project', nargs="?", help='Project directory', default=".")
args = parser.parse_args()

if args.debug:
    MONJOUR_DEBUG = 'True'
    os.environ['MONJOUR_DEBUG'] = MONJOUR_DEBUG

if args.log_level:
    MONJOUR_LOG_LEVEL = args.log_level
    os.environ['MONJOUR_LOG_LEVEL'] = MONJOUR_LOG_LEVEL

if args.demo:
    demo_dev_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'demo_dev'))
    if os.path.exists(os.path.join(demo_dev_dir, 'configuration.py')):
        proj_dir = demo_dev_dir
        log.info("Running the demo in development mode")
    else:
        proj_dir = resources.files('monjour').joinpath('demo')
    proj_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'demo'))
    log.info("Running the demo")
else:
    if args.project == ".":
        proj_dir = os.path.realpath(os.getcwd())
    else:
        proj_dir = os.path.realpath(args.project)

if not os.path.isdir(proj_dir):
    raise SystemExit(f"Error: Project directory '{proj_dir}' does not exist")
os.environ['MONJOUR_ORIGINAL_CWD'] = os.getcwd()
os.environ['MONJOUR_PROJECT_DIR'] = proj_dir
os.chdir(proj_dir)
log.info(f"Changed working directory to {os.getcwd()}")
sys.path.append(proj_dir)

if args.Xapp:
    json_args = {}
    for arg in args.Xapp:
        key, value = arg[0].split('=')
        json_args[key] = value
    os.environ['MONJOUR_APP_ARGS'] = json.dumps(json_args)

if args.streamlit or args.demo:
    import streamlit.web.cli as stcli
    import streamlit as st

    app_entry_file = os.path.join( os.path.dirname(__file__), 'st', 'st_main.py')
    sys.argv = ["streamlit", "run", app_entry_file]

    if args.Xstreamlit:
        for arg in args.Xstreamlit:
            sys.argv.append("--" + arg)

    # This will start the server on this thread and
    # run the streamlit script on a different thread
    stcli.main()
else:
    print("For now only Streamlit is supported. Re-run with --st to start the streamlit server.")