import pandas as pd
import streamlit as st

from monjour.st import monjour_app_cache, StApp, get_st_app

st_app = get_st_app(st.session_state.project_dir)

@monjour_app_cache(st_app, key='line_df')
def line_chart_df(df: pd.DataFrame):
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    df_daily = df.groupby('month')['amount'].sum().reset_index()
    return df_daily

