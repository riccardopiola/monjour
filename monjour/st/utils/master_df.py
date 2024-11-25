import pandas as pd
import streamlit as st

from monjour.st import monjour_app_cache, StApp
from monjour.core.transaction import Transaction

from monjour.st.components.common.df_explorer import df_explorer

MAIN_DF_COLUMNS = Transaction.get_attribute_names()

MAIN_DF_RELEVANT_COLUMNS = [
    'date',
    'amount',
    'currency',
    'account_id',
    'category'
    'notes',
    'desc',
    'counterpart',
    'location',
    'payment_type',
    'payment_type_details',
    'ref',
    'extra',
    'archive_id',
]

def get_column_config(st_app: StApp):
    column_config = {
        'date': st.column_config.DatetimeColumn(label='Date'),
        'amount': st.column_config.NumberColumn(label='Amount', format='%.2f'),
        'currency': st.column_config.Column(label='Currency'),
        'account_id': st.column_config.Column(label='Account ID'),
        'category': st.column_config.Column(label='Category'),
        'notes': st.column_config.Column(label='Notes'),
        'desc': st.column_config.Column(label='Description'),
        'counterpart': st.column_config.Column(label='Counterpart'),
        'location': st.column_config.Column(label='Location'),
        'payment_type': st.column_config.Column(label='Payment Type'),
        'payment_type_details': st.column_config.Column(label='Payment Type Details'),
        'ref': st.column_config.Column(label='Ref'),
        'extra': st.column_config.Column(label='Extra'),
        'archive_id': st.column_config.Column(label='Archive ID'),
    }
    return column_config
