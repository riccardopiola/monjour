from typing import Any
import streamlit as st
import datetime as dt
import pandas as pd
import plotly.express as px

from monjour.st import get_st_app
from monjour.st.utils import key_combine

from monjour.st.components.visualization import income_expenses
from monjour.st.components.common.df_explorer import df_date_filter

st_app = get_st_app(st.session_state.project_dir)

st.header("Income/Expenses Report")
week_month: Any = st.segmented_control('Divide by', ['Week', 'Month', 'Day'],
                    key=key_combine(__name__, 'week_month'), default='Month')

df = df_date_filter(st_app.app.df, key=__name__)
df = df.copy()

df['expense'] = df['amount'] < 0
df['day'] = df['date'].dt.to_period('D').apply(lambda r: r.start_time)
df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
df['month'] = df['date'].dt.to_period('M').apply(lambda r: r.start_time)
df['amount_abs'] = df['amount'].abs()
df = df.sort_values('date')

fig = income_expenses.income_expense(df, week_month=week_month.lower())
st.plotly_chart(fig, use_container_width=True)


fig = income_expenses.balance(df, week_month=week_month.lower())
st.plotly_chart(fig, use_container_width=True)

# fig = income_expenses.balance_cum(df)
# st.plotly_chart(fig, use_container_width=True)

fig = income_expenses.expense_by_day_of_the_week(df)
st.plotly_chart(fig, use_container_width=True)

st.write("Add decomposition of income. Interest etc...")