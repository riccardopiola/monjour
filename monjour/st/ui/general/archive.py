import streamlit as st
import pandas as pd
import os

from monjour.core.importer import ImportContext
from monjour.core.archive import WriteOnlyArchive

from monjour.st import get_st_app
from monjour.st.components.archive_editor import archive_editor
from monjour.st.components.file_import import file_import_options, new_key

st_app = get_st_app(st.session_state.project_dir)
app = st_app.app

st.title("Archive")

records = sorted(app.archive.records.values(), key=lambda r: r['imported_date'], reverse=True)
if len(records) > 0:
    last_imported_date = records[0]['imported_date'].strftime("%Y-%m-%d %H:%M:%S")
else:
    last_imported_date = "No files imported yet"

st.table([
    ("Archive directory", os.path.realpath(str(app.archive.archive_dir))),
    ("Last imported date", last_imported_date)
])

"""
### Archive Management
Here you can delete files previously imported via the streamlit interface.
"""

archive_editor(st_app)

st.subheader("Import new file")
import_ctx: ImportContext|None = None

def import_form():
    with st.container(border=True):
        if (options := file_import_options(st_app, key=__name__)) is not None:
            # Submit button
            c1, c2, c3 = st.columns(3)
            if c1.button('Import', type='primary', use_container_width=True, key=new_key(__name__)):
                return options, 'import'
            if c2.button('Preview', type='secondary', use_container_width=True, key=new_key(__name__)):
                return options, 'preview'
            if c3.button('Cancel', type='secondary', use_container_width=True, key=new_key(__name__)):
                return None
    return None

def import_result(import_ctx: ImportContext, result: pd.DataFrame):
    account = import_ctx.account
    st.dataframe(result[account.COLUMN_ORDER])

form_result = import_form()

if form_result is None:
    pass
elif form_result[1] == 'import':
    options = form_result[0]
    if import_ctx is None:
        import_ctx = st_app.app._archive_file(
            account_id=options.account.id,
            file=options.file,
            filename=options.file.name,
            date_range=options.date_range,
        )

    # In rare cases result is None and the function archive_file function
    # did not throw.
    if import_ctx.result is not None:
        import_ctx.st_show_diagnostics()
        st.success(f'File "{options.file.name}" imported successfully.')
        st.write("### Import result")
        import_result(import_ctx, import_ctx.result)

elif form_result[1] == 'preview':
    options = form_result[0]
    account_id = options.account.id

    # Create a copy of the app with a WriteOnlyArchive
    preview_app = st_app.app.copy()
    preview_app.archive = WriteOnlyArchive('/')

    # Make a copy only of the account we are interested in
    preview_app.accounts[account_id] = preview_app.accounts[account_id].copy()

    if import_ctx is None:
        import_ctx = preview_app._archive_file(
            account_id=account_id,
            file=options.file,
            filename=options.file.name,
            date_range=options.date_range,
        )

    if import_ctx.result is not None:
        import_ctx.st_show_diagnostics()
        st.write("### Import (preview)")
        import_result(import_ctx, import_ctx.result)

