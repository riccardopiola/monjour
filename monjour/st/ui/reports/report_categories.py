from typing import Any
import streamlit as st
import datetime as dt
import pandas as pd
import plotly.express as px

from monjour.st import get_st_app
from monjour.st.utils import key_combine

from monjour.st.components.common.df_explorer import df_date_filter
from monjour.st.components.visualization import income_expenses
from monjour.st.components.visualization import sankey

st_app = get_st_app(st.session_state.project_dir)

st.title("Categories Report")
df = df_date_filter(st_app.app.df, key=__name__)
df = df.copy()

# TODO: Remove this hack and implement it with an importer
df['category'] = df['category'].str.replace('.', '/')

# Aggregate total expenses by category
category_data = (
    df.groupby('category')
    .agg({ 'category': 'count', 'amount': 'sum' })
    .rename(columns={'category': 'count'})
    .reset_index()
)
category_data['enable'] = True
category_data['expense'] = category_data['category'].str.startswith('Expense')
category_data['amount_abs'] = category_data['amount'].abs()
category_data = category_data.sort_values('amount_abs', ascending=False)

# Eliminate the first level of the category hierarchy for better visualization
category_data['category_flat'] = category_data['category'].str.split('/').str[1:].str.join('/')

expenses = category_data[category_data['expense']]
income = category_data[~category_data['expense']]

##############################################
# Tables
##############################################

column_order=['enable', 'category_flat', 'count', 'amount_abs']
column_config = {
    'amount_abs': st.column_config.NumberColumn(label="Total", format='%.2f', disabled=True),
    'category_flat': st.column_config.TextColumn(label="Expense Category", disabled=True),
    'count': st.column_config.NumberColumn(label="#", disabled=True),
    'enable': st.column_config.CheckboxColumn(label="Enable", width='small'),
}

c1, c2 = st.columns(2)
with c1:
    st.subheader("Income Categories")
    income_filter = st.data_editor(income, use_container_width=True, hide_index=True, column_config=column_config,
        key=key_combine(__name__, 'income_selector'), column_order=column_order)

with c2:
    st.subheader("Expense Categories")
    expense_filter = st.data_editor(expenses, use_container_width=True, hide_index=True, column_config=column_config,
        key=key_combine(__name__, 'expense_selector'), column_order=column_order)

# Filter the data based on the user selection
enabled_income = income[income_filter['enable']]
enabled_expenses = expenses[expense_filter['enable']]

##############################################
# Sunburst charts
##############################################

# A sunburst chart is like a pie chart but with multiple levels
c1, c2 = st.columns(2)
with c1:
    fig = px.sunburst(
        enabled_income,
        path=['category_flat'],  # Define the hierarchy
        values='amount_abs',
        title='Income Distribution by Category',
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True, height=600)
with c2:
    fig = px.sunburst(
        enabled_expenses,
        path=['category_flat'],  # Define the hierarchy
        values='amount_abs',
        title='Expense Distribution by Category',
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True, height=600)

##############################################
# Sankey diagram
##############################################

# Draw the Sankey diagram
fig = sankey.sankey(income, expenses)
st.plotly_chart(fig, use_container_width=True, height=600)

