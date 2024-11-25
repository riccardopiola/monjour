import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode, JsCode

from monjour.st import get_st_app
from monjour.core.account import Account

from monjour.st.components.common.df_explorer import df_explorer, df_date_filter

st_app = get_st_app(st.session_state.project_dir)

st.title("Data Editor")

df = st_app.app.df[[ 'date', 'amount', 'currency', 'category', 'desc', 'notes', 'counterpart', 'location', ]]


df = df_explorer(df)
df = df_date_filter(df, key=__name__)
st.data_editor(df, height=800)