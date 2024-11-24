import streamlit as st
from typing import Literal

import monjour.core.log as log
from monjour.app import App
from monjour.core.importer import ImportContext
from monjour.core.common import DateRange
from monjour.core.archive import WriteOnlyArchive

from monjour.st import get_st_app
from monjour.st.components.file_import import file_import_options, FileImportOptions

st_app = get_st_app(st.session_state.project_dir)

def import_form():
    with st.container(border=True):
        if (options := file_import_options(st_app, key=__name__)) is not None:
            # Submit button
            c1, c2, c3 = st.columns(3)
            if c1.button('Import', type='primary', use_container_width=True, key=new_key(__name__)):
                return options, 'import'
            if c2.button('Preview', type='secondary', use_container_width=True, key=new_key(__name__)):):
                return options, 'preview'
            if c3.button('Cancel', type='secondary', use_container_width=True, key=new_key(__name__)):):
                return None
    return None

def import_result(import_ctx: ImportContext):
    what = st.radio('What to show', ['Imported file contents', 'Contents merged into account'], index=0, key='import_result', horizontal=True)

    account = import_ctx.account
    if what == 'Account':
        st.dataframe(account.data[account.COLUMN_ORDER])
    elif (result := import_ctx.result) is not None:
        # Not all importr_ctx have result available (depends on whether they use an executor)
        st.dataframe(result[account.COLUMN_ORDER])
    else:
        # More expensive operation than above but ultimately the same
        st.dataframe(account.data[account.data['archive_id'] == import_ctx.archive_id][account.COLUMN_ORDER])


st.write('### Import a new file')
import_ctx: ImportContext|None = None
prev_mode: Literal['import', 'preview', None] = None
form_result = import_form()
if form_result != prev_mode:
    import_ctx = None

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

    if import_ctx is not None:
        st.success(f'File "{options.file.name}" imported successfully.')
        import_ctx.st_show_diagnostics()
        st.write("### Import result")
        import_result(import_ctx)

elif form_result[1] == 'preview':
    options = form_result[0]
    preview_app = st_app.app.copy()
    preview_app.archive = WriteOnlyArchive('/')

    if import_ctx is None:
        import_ctx = preview_app._archive_file(
            account_id=options.account.id,
            file=options.file,
            filename=options.file.name,
            date_range=options.date_range,
        )

    if import_ctx is not None:
        st.write("### Import (preview)")
        import_result(import_ctx)

