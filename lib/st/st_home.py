import importlib
import os
from lib.app import App, DateRange

import streamlit as st

# Import the module named configuration.py
config_file_path = os.path.join(os.path.curdir, 'configuration.py')
config_module_name = 'configuration'
config_module = importlib.import_module(config_module_name, config_file_path)

# Import the app from the configuration module
app: App = config_module.app

st.title('Hello, Streamlit!')
st.write('This is a demo of Streamlit running in a separate process.')
