import streamlit as st
import pandas as pd
from typing import Any

from monjour.core.archive import InMemoryArchive, WriteOnlyArchive, Archive
from monjour.core.importer import ImportContext
from monjour.utils.debug_executor import DebugExecutor, Executor

from monjour.st.components.file_import import FileImportOptions, file_import_options
from monjour.st import get_st_app

main_app = get_st_app(st.session_state.project_dir)

@st.cache_resource
def _app_for_import():
    st_app = main_app.copy('tmp')
    st_app.app.archive = WriteOnlyArchive('/')
    return st_app

def display_debug_ctx(executor: Executor[Any, pd.DataFrame]):
    if not isinstance(executor, DebugExecutor):
        raise Exception('The executor is not a DebugExecutor')
    if executor.last_block is None:
        return
    total_transformations = len(executor.last_block.transformation_decls)
    transformations_applied = len(executor.last_block.transformations)
    if total_transformations != transformations_applied:
        st.warning('Not all transformations have been applied')
        st.code(f"""\
Total transformations: {total_transformations}
Transformations applied: {transformations_applied}

The following transformations have not been applied:
{'\n'.join([f"- {t.name}" for t in executor.last_block.transformation_decls[transformations_applied:]])}
        """)
    else:
        st.success('All transformations have been applied without errors')

    transformation = st.radio('Examine a transformation', executor.last_block.transformations,
        format_func=lambda t: t.name)

    if transformation is None:
        return
    input = transformation.args[1]
    output = transformation.result
    (c1, c2) = st.columns(2)
    c1.write("#### Input")
    c1.dataframe(input)
    c2.write("#### Output")
    c2.dataframe(output)

    st.write("#### Comparison")
    st.dataframe(input.compare(output))


debug_what = st.radio('Process to debug', ['Import'], index=0)

if debug_what == 'Import':
    debug_app = _app_for_import()
    if (options := file_import_options(debug_app)) is not None:
        fatal_error = None
        if not 'executor' in st.session_state:
            st.session_state.executor = DebugExecutor()
        if st.button('Debug Import', type='primary'):
            with st.spinner('Importing...'):
                st.session_state.executor.reset()
                try:
                    debug_app.app._archive_file(
                        account_id=options.account.id,
                        file=options.file,
                        filename='debug',
                        date_range=options.date_range,
                        executor=st.session_state.executor,
                    )
                except Exception as e:
                    fatal_error = e
        # Try to display the debug context even if an error occurred
        display_debug_ctx(st.session_state.executor)
        if fatal_error is not None:
            st.error("Import failed due to a fatal error")
            raise fatal_error
        else:
            st.success('Imported successfully')

