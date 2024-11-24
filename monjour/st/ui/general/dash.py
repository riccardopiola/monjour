import streamlit as st
import pandas as pd
from streamlit_extras.add_vertical_space import add_vertical_space

from monjour.st import get_st_app, monjour_app_cache

from monjour.st.components.df_explorer import df_explorer
from monjour.st.components.archive_editor import archive_editor
from monjour.st.components.master_df import get_column_config, MASTER_DF_RELEVANT_COLUMNS

from monjour.st.st_views import line_chart_df

st_app = get_st_app(st.session_state.project_dir)
app = st_app.app

st.title("Dashboard")

# Use an editable dataframe where users can select the rows they want to delete

# st.write("##### Database info")
c1, c2, c3 = st.columns(3)
c1.metric("Transactions", len(st_app.app.df))
c2.metric("Accounts", len(st_app.app.accounts))
c3.metric("Files imported", len(st_app.app.archive.records))

# add_vertical_space(1)
st.write("#### Monthly spending trend")
add_vertical_space(1)


st.line_chart(
    line_chart_df(st_app.app.df),
    x='month', y='amount',
    x_label='Time', y_label='Monthly Balance',
    width=1000
)

st.subheader("Accounts summary")
records_df = pd.DataFrame.from_records(list(app.archive.records.values()))
accounts_df = app.df.groupby('account_id').agg({'amount': 'sum'}).reset_index()

df = records_df.merge(accounts_df, left_on='account_id', right_on='account_id', how='left', suffixes=('_records', '_accounts'))
# st.dataframe(df[['account_id', 'amount']])
st.dataframe(df)

st.subheader("Transactions")
filtered_df = df_explorer(st_app.app.df)

c1, c2, c3 = st.columns([0.4, 0.2, 0.3], vertical_alignment='center')
options = ['All', 'Last year', 'Last 90 Days' ]
selection = c1.segmented_control('Date range', options, key='home_date_range',
            label_visibility='visible', default='All', selection_mode='single')
limit_enabled = c2.toggle('Limit', key='home_limit', value=True)
limit_num = c3.number_input('Number of transactions', min_value=1, key='home_limit_value', value=100)
match selection:
    case 'Last year':
        filtered_df = filtered_df[filtered_df['date'] >= pd.Timestamp.now() - pd.DateOffset(years=1)]
    case 'Last 90 Days':
        filtered_df = filtered_df[filtered_df['date'] >= pd.Timestamp.now() - pd.DateOffset(days=90)]
if limit_enabled:
    filtered_df = filtered_df.head(limit_num)
st.dataframe(filtered_df, column_config=get_column_config(st_app), column_order=MASTER_DF_RELEVANT_COLUMNS,
             hide_index=True, height=1000)

st.write(f"Showing {len(filtered_df)} transactions of {len(st_app.app.df)} total transactions.")