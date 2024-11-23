import streamlit as st
import pandas as pd
import numpy as np
from streamlit_ace import st_ace

from monjour.st import get_st_app

main_app = get_st_app(st.session_state.project_dir)

def exec_block(content: str):
    app = main_app.copy('jupyter')

    class Out:
        def __init__(self):
            self.parent = None

        def header(self, *args, **kwargs):
            st.header(*args, **kwargs)

        def subheader(self, *args, **kwargs):
            st.subheader(*args, **kwargs)

        def write(self, *args, **kwargs):
            st.write(*args, **kwargs)

        def __lshift__(self, value):
            st.write(value) # type: ignore

        @property
        def section(self):
            return st.container(border=True)

    out = Out()
    # with st.container(border=True):
    # st.write('### Output')
    exec(content, { 'out': out, 'print': out.write, 'app': app.app, 'st': st, 'pd': pd, 'np': np })

def block(i: int):
    name = f"debug_jupyter_content_{i}"
    if not name in st.session_state:
        st.session_state[name] = ''

    content = st_ace(
        value=st.session_state[name],
        language='python',
        theme='monokai',
        key=name + '_ace',
    )

    st.session_state.debug_jupyter_content = content
    exec_block(st.session_state.debug_jupyter_content)


st.markdown("""
Globals:
- `out`: Output object
- `print`: Output.write
- `app`: App object
- `st`: streamlit
- `pd`: pandas
- `np`: numpy
""")

n_blocks = 1
for i in range(n_blocks):
    block(i)
