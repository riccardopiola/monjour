import streamlit as st
import pandas as pd
import os
from typing import Literal

from monjour.core.importer import ImportContext
from monjour.core.archive import WriteOnlyArchive

from monjour.st import get_st_app
from monjour.st.components.general.archive_editor import archive_editor
from monjour.st.components.general.file_import import file_import_options

from monjour.st.utils import use_state, key_combine

st_app = get_st_app(st.session_state.project_dir)
app = st_app.app

######################################
# Archive summary
######################################

st.title("Archive")

records = sorted(app.archive.records.values(), key=lambda r: r['imported_date'], reverse=True)
if len(records) > 0:
    last_imported_date = records[0]['imported_date'].strftime("%Y-%m-%d %H:%M:%S")
else:
    last_imported_date = "No files imported yet"

with st.container(border=True):
    c1, c2 = st.columns([1, 2], vertical_alignment='bottom')
    c1.write("Archive directory:")
    c2.write(f"`{os.path.realpath(str(app.archive.archive_dir))}`")
    c1.write("Last imported date:")
    c2.write(f"`{last_imported_date}`")

######################################
# Archive management
######################################

st.subheader("Archive management")
st.write("Here you can delete files previously imported via the streamlit interface.")
archive_editor(st_app, __name__)

######################################
# Import new file
######################################

st.subheader("Import new file")

def import_form():
    with st.container(border=True):
        if (options := file_import_options(st_app, page=__name__)) is not None:
            # Submit button
            c1, c2, c3 = st.columns(3)
            if c1.button('Import', type='primary', use_container_width=True, key=key_combine(__name__, 'import')):
                return options, 'import'
            if c2.button('Preview', type='secondary', use_container_width=True, key=key_combine(__name__, 'preview')):
                return options, 'preview'
            if c3.button('Cancel', type='secondary', use_container_width=True, key=key_combine(__name__, 'cancel')):
                return None
    return None

def import_result(import_ctx: ImportContext, result: pd.DataFrame):
    account = import_ctx.account
    st.dataframe(result[account.COLUMN_ORDER], hide_index=True)

import_ctx = use_state[ImportContext|None](__name__, 'import_ctx', lambda: None)
form_result = import_form()

if form_result is None:
    pass
elif form_result[1] == 'import':
    options = form_result[0]
    if import_ctx.get() is None:
        import_ctx.set(
                st_app.app._archive_file(
                account_id=options.account.id,
                file=options.file,
                filename=options.file.name,
                date_range=options.date_range,
            )
        )

    # In rare cases result is None and the function archive_file function
    # did not throw.
    ctx = import_ctx.get() # type: ignore
    if ctx is not None and ctx.result is not None:
        ctx.st_show_diagnostics()
        st.success(f'File "{options.file.name}" imported successfully.')
        st.write("### Import result")
        import_result(ctx, ctx.result)

elif form_result[1] == 'preview':
    options = form_result[0]
    account_id = options.account.id

    # Create a copy of the app with a WriteOnlyArchive
    preview_app = st_app.app.copy()
    preview_app.archive = WriteOnlyArchive('/')

    # Make a copy only of the account we are interested in
    preview_app.accounts[account_id] = preview_app.accounts[account_id].copy()

    if import_ctx.get() is None:
        import_ctx.set(
            preview_app._archive_file(
                account_id=options.account.id,
                file=options.file,
                filename=options.file.name,
                date_range=options.date_range,
            )
        )

    ctx: ImportContext|None = import_ctx.get() # type: ignore
    if ctx is not None and ctx.result is not None:
        ctx.st_show_diagnostics()
        st.write("### Import (preview)")
        import_result(ctx, ctx.result)

