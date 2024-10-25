import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--init', action='store_true', help='Initialize a project in the current directory')
parser.add_argument('--demo', type=str, help='Run the demo')
parser.add_argument('-st', '--streamlit', action='store_true', help='Run the Streamlit server')
parser.add_argument('--console', action='store_true', help='Launch the separate admin console')
args = parser.parse_args()

if args.streamlit:
    from lib.st import st_main
    st_main()