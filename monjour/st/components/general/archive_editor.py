import streamlit as st
import pandas as pd

from monjour.st import StApp
from monjour.st.utils import use_state

def archive_editor(st_app: StApp, page: str):
    msgs = use_state(page, 'archive_messages', list).get()
    df = st_app.app.archive.df # already cached by archive

    st.data_editor(
        df,
        hide_index=True,
        num_rows="dynamic",
        column_order=['selected', 'imported_date', 'account_id', 'is_managed_by_archive', 'file_path', 'date_start', 'date_end', 'id'],
        column_config={
            'selected': st.column_config.Column(disabled=True),
            'imported_date': st.column_config.Column(disabled=True),
            'account_id': st.column_config.Column(disabled=True),
            'is_managed_by_archive': st.column_config.Column(disabled=True),
            'file_path': st.column_config.Column(disabled=True),
            'date_start': st.column_config.Column(disabled=True),
            'date_end': st.column_config.Column(disabled=True),
            'id': st.column_config.Column(disabled=True),
        },
        key='archive_editor'
    )

    added_rows = st.session_state.archive_editor['added_rows']
    deleted_rows = st.session_state.archive_editor['deleted_rows']
    if len(added_rows) > 0:
        st.error("You cannot add new records to the archive directly. Import the file instead. Reload the page to clear the added rows.")
        st.session_state.archive_editor['added_rows'] = []
    if len(deleted_rows) > 0:
        for idx in deleted_rows:
            record = df.iloc[idx].to_dict()
            if not record['is_managed_by_archive']:
                msgs.append(lambda: st.error(f"You cannot remove {record['id']} from the archive as it is managed externally. Reload the page to reset the deleted rows."))
            else:
                msgs.append(lambda: st.info(f"Removed {record['id']} from the archive"))
                st_app.app.archive.forget_file(record['id'])
        st.session_state.archive_editor['deleted_rows'] = []

    for msg in msgs:
        msg()
