from typing import Any
import streamlit as st
import datetime as dt
import pandas as pd
import plotly.express as px

from monjour.st import get_st_app
from monjour.st.utils import key_combine

from monjour.st.components.common.df_explorer import df_date_filter
from monjour.st.components.visualization import income_expenses
from monjour.st.components.visualization.sankey import sankey_diagram

st_app = get_st_app(st.session_state.project_dir)

st.title("Categories Report")
df = df_date_filter(st_app.app.df, key=__name__)
df = df.copy()

# week_month: Any = st.segmented_control('Divide by', ['Week', 'Month', 'Day'],
#                     key=key_combine(__name__, 'week_month'), default='Month')


# TODO: Remove this hack and implement it with an importer
df['category'] = df['category'].str.replace('.', '/')
df['expense'] = df['amount'] < 0
df['amount_abs'] = df['amount'].abs()

expenses = df[df['expense']]
income = df[~df['expense']]

# Aggregate total expenses by category
category_data = (
    expenses.groupby('category')
    .agg({ 'category': 'count', 'amount_abs': 'sum' })
    .rename(columns={'category': 'count'})
    .sort_values('amount_abs', ascending=False)
    .reset_index()
)
category_data['enable'] = True
category_data['category'] = category_data['category'].str.split('/').str[1:].str.join('/')

st.subheader("Expenses")
category_data = st.data_editor(category_data, use_container_width=True, hide_index=True, column_config={
    'amount_abs': st.column_config.NumberColumn(label="Total", format='%.2f', disabled=True),
    'category': st.column_config.TextColumn(label="Expense Category", disabled=True),
    'count': st.column_config.NumberColumn(label="# transactions", disabled=True),
    'enable': st.column_config.CheckboxColumn(label="Enable", width='small')
}, key=key_combine(__name__, 'category_selector'), column_order=['enable', 'category', 'count', 'amount_abs'])

category_data = category_data[category_data['enable']]

# A sunburst chart is like a pie chart but with multiple levels
fig = px.sunburst(
    category_data,
    path=['category'],  # Define the hierarchy
    values='amount_abs',
    title='Expense Distribution by Category',
    template='plotly_white'
)

st.plotly_chart(fig, use_container_width=True, height=600)

# Draw the Sankey diagram
sankey_diagram(df)
st.plotly_chart(sankey_diagram(df), use_container_width=True, height=600)
