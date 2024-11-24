import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode, JsCode

from monjour.st import get_st_app
from monjour.core.account import Account

st_app = get_st_app(st.session_state.project_dir)

df = st_app.app.df[[ 'date', 'amount', 'currency', 'category', 'desc', 'notes', 'counterpart', 'location', ]]

st.write("Edit your dataframe")

st.data_editor(df)

