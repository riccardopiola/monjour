import pandas as pd
import streamlit as st

from monjour.st import monjour_app_cache, StApp, get_st_app

@monjour_app_cache(key='line_chart_df')
def line_chart_df(st_app: StApp):
    df = st_app.app.df
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    df_daily = df.groupby('month')['amount'].sum().reset_index()
    return df_daily

