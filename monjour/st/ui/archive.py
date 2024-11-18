import streamlit as st
import pandas as pd

from monjour.st import StApp

st_app = StApp(st.session_state.project_dir)
archive = st_app.app.archive

st.title('Archive')

archive_df = pd.DataFrame.from_dict(archive.records, orient='index')
st.dataframe(archive_df, hide_index=True)