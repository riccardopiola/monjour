import streamlit as st
import pandas as pd
from typing import Any

from monjour.core.archive import InMemoryArchive, WriteOnlyArchive, Archive
from monjour.core.importer import ImportContext
from monjour.utils.debug_executor import DebugExecutor, Executor

from monjour.st import get_st_app
from monjour.st.utils import df_drop_empty_columns, df_show_first
from monjour.st.components.file_import import FileImportOptions, file_import_options
from monjour.st.components.diff import show_diff

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

    c1, c2 = st.columns(2)
    transformation = c1.radio('Examine a transformation', executor.last_block.transformations,
        format_func=lambda t: t.name)
    show_inout = c2.toggle('Show input/output', False)
    show_comparison = c2.toggle('Show comparison', True)
    do_drop_empty_cols = c2.toggle('Drop empty columns', False)
    show_all = c2.toggle('Show all', False)
    n = c2.number_input('Show first n rows', min_value=-1, value=10)

    if transformation is None:
        st.error("Nothing can be shown")

    input: pd.DataFrame = transformation.args[1]
    output: pd.DataFrame = transformation.result

    if show_inout:
        inout_in = input
        inout_out = output
        if do_drop_empty_cols:
            inout_in = input.dropna(axis=1, how='all')
            inout_out = output.dropna(axis=1, how='all')
        if not show_all:
            inout_in = inout_in.head(n)
            inout_out = inout_out.head(n)
        (c1, c2) = st.columns(2)
        c1.write("#### Input")
        c1.dataframe(inout_in)
        c2.write("#### Output")
        c2.dataframe(inout_out)

    if show_comparison:
        show_diff(input, output)


debug_what = st.radio('Process to debug', ['Import'], index=0, horizontal=True)

if debug_what == 'Import':
    debug_app = _app_for_import()
    fatal_error = None
    if not 'debug_executor' in st.session_state:
        st.session_state.debug_executor = DebugExecutor()
    with st.container(border=True):
        if (options := file_import_options(debug_app)) is not None:
            c1, c2 = st.columns(2)
            if c1.button('Reset', use_container_width=True, key='debug-reset'):
                st.session_state.debug_executor.reset()
            if c2.button('Debug Import', type='primary', use_container_width=True):
                with st.spinner('Importing...'):
                    st.session_state.debug_executor.reset()
                    try:
                        debug_app.app._archive_file(
                            account_id=options.account.id,
                            file=options.file,
                            filename='debug',
                            date_range=options.date_range,
                            executor=st.session_state.debug_executor,
                        )
                    except Exception as e:
                        fatal_error = e
    # Try to display the debug context even if an error occurred
    display_debug_ctx(st.session_state.debug_executor)
    if fatal_error is not None:
        st.error("Import failed due to a fatal error")
        raise fatal_error

