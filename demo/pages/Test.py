import streamlit as st
import plotly.express as px
from monjour.st import get_st_app

st_app = get_st_app(st.session_state.project_dir)
df = st_app.app.df.copy()

st.title("Demo report")

# st.dataframe(df.head(50))
fig = px.histogram(df, x='amount', nbins=50)

st.plotly_chart(fig)