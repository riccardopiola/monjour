import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_extras.add_vertical_space import add_vertical_space

from monjour.st import get_st_app, StApp

from monjour.st.components.common.df_explorer import df_explorer, df_date_filter
from monjour.st.utils.master_df import get_column_config, MAIN_DF_RELEVANT_COLUMNS

from monjour.st.utils import cache

st_app = get_st_app(st.session_state.project_dir)
app = st_app.app

st.title("Dashboard")

#####################################
# Metrics
#####################################

c1, c2, c3 = st.columns(3)
c1.metric("Transactions", len(st_app.app.df))
c2.metric("Accounts", len(st_app.app.accounts))
c3.metric("Files imported", len(st_app.app.archive.records))

#####################################
# Spending trend
#####################################

@cache.monjour_app_cache(key='dash_freqency_chart')
def freqency_chart(st_app: StApp):
    df = st_app.app.df
    df = df.copy()
    df['day'] = df['date'].dt.to_period('D').apply(lambda r: r.start_time)
    by_day = df.groupby('day').agg({'day': 'count'}).rename(columns={'day': 'count'}).reset_index()
    fig = px.histogram(
        by_day,
        x='day',
        y='count',
        title='Transactions per day',
        labels={'count': 'Number of transactions', 'day': 'Day'},
        # template='plotly_white',
        nbins=100
    )
    fig.update_traces(
        marker=dict(
            colorscale='Viridis',  # Choose a vibrant color scale
            line=dict(color='black', width=1.5),  # Add black outlines
            opacity=0.8
        )
    )
    return fig

st.plotly_chart(freqency_chart(st_app), use_container_width=True)

#####################################
# Accounts summary
#####################################

st.subheader("Accounts summary")
records_df = app.archive.df.groupby('account_id').agg(
    last_uploaded=('imported_date', 'max'),
    num_records=('account_id', 'count')
)
accounts_df = app.df.groupby('account_id').agg(
    balance=('amount', 'sum'),
    last=('date', 'max'),
    first=('date', 'min')
)
account_names = pd.DataFrame.from_records([{
    'account_id': acc.id,
    'name': acc.name,
    'provider': acc.PROVIDER_ID
} for acc in app.accounts.values()])

df = records_df.merge(accounts_df, left_on='account_id', right_on='account_id', how='left')
df = df.merge(account_names, left_on='account_id', right_on='account_id', how='left')

st.dataframe(df[['account_id', 'name', 'provider', 'num_records', 'last_uploaded', 'last', 'first', 'balance']], column_config={
    'account_id': st.column_config.Column(label='ID'),
    'name': st.column_config.Column(label='Name'),
    'provider': st.column_config.Column(label='Provider'),
    'num_records': st.column_config.NumberColumn(label='Files', help='Number of files imported for this account'),
    'last_uploaded': st.column_config.DateColumn(label='Last uploaded', help='Last time a file was imported for this account'),
    'first': st.column_config.DateColumn(label='First', help='Date of the first transaction from this account'),
    'last': st.column_config.DateColumn(label='Last', help='Date of the last transaction from this account'),
    'balance': st.column_config.NumberColumn(label='Balance'),
}, hide_index=True, use_container_width=True)

#####################################
# Transactions
#####################################

add_vertical_space(1)
st.subheader("Transactions")
filtered_df = df_explorer(st_app.app.df)

c1, c2, c3 = st.columns([0.4, 0.2, 0.3], vertical_alignment='center')
with c1:
    filtered_df = df_date_filter(filtered_df, key='dash', options=['All', 'Last year', 'Last 90 Days'])
with c2:
    limit_enabled = c2.toggle('Limit', key='home_limit', value=True)
with c3:
    limit_num = c3.number_input('Number of transactions', min_value=1, key='home_limit_value', value=100)

# Apply limit if only when toggle is enabled
if limit_enabled:
    filtered_df = filtered_df.head(limit_num)

filtered_df = filtered_df.reset_index()
st.dataframe(filtered_df, column_config=get_column_config(st_app), column_order=MAIN_DF_RELEVANT_COLUMNS + ['deterministic_id'],
             hide_index=True, height=1000)

st.write(f"Showing {len(filtered_df)} transactions of {len(st_app.app.df)} total transactions.")