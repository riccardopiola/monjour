import streamlit as st
import pandas as pd
from typing import Any

from monjour.core.archive import WriteOnlyArchive
from monjour.core.executor import RecordingExecutor

from monjour.st import get_st_app
from monjour.st.components.file_import import FileImportOptions, file_import_options
from monjour.st.components.diff import show_diff

main_app = get_st_app(st.session_state.project_dir)

@st.cache_resource
def _app_for_import():
    st_app = main_app.copy('tmp')
    st_app.app.archive = WriteOnlyArchive('/')
    return st_app

def display_debug_ctx(executor: RecordingExecutor[Any, pd.DataFrame]):
    all_transformations = executor.get_all_transformations()

    st.write(f"Found {len(all_transformations)} transformations")

    c1, c2 = st.columns(2)
    transformation_index = c1.radio('Examine a transformation', range(0, len(all_transformations)),
                                   format_func=lambda i: all_transformations[i].name)
    transformation = all_transformations[transformation_index]
    show_inout = c2.toggle('Show input/output', True)
    show_comparison = c2.toggle('Show comparison', False)
    do_drop_empty_cols = c2.toggle('Drop empty columns', False)
    show_all = c2.toggle('Show all', False)
    n = c2.number_input('Show first n rows', min_value=-1, value=10)

    if transformation is None:
        st.error("Nothing can be shown")
        return

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
        # Write n rows and n columns
        c1.write(f"Shape: {input.shape} (showing {inout_in.shape[0]} rows)")
        c2.write("#### Output")
        c2.dataframe(inout_out)
        c2.write(f"Shape: {output.shape} (showing {inout_out.shape[0]} rows)")

    if show_comparison:
        show_diff(input, output)


debug_what = st.radio('Process to debug', ['Import', 'Merge'], index=0, horizontal=True)

if not 'debug_executor' in st.session_state:
    st.session_state.debug_executor = RecordingExecutor()

if debug_what == 'Import':
    debug_app = _app_for_import()
    fatal_error = None
    with st.container(border=True):
        if (options := file_import_options(debug_app)) is not None:
            c1, c2 = st.columns(2)
            if c1.button('Reset', use_container_width=True, key='debug-reset'):
                st.session_state.debug_executor = RecordingExecutor()
            if c2.button('Debug Import', type='primary', use_container_width=True):
                with st.spinner('Importing...'):
                    st.session_state.debug_executor = RecordingExecutor()
                    try:
                        debug_app.app._archive_file(
                            account_id=options.account.id,
                            file=options.file,
                            filename=options.file.name,
                            date_range=options.date_range,
                            executor=st.session_state.debug_executor,
                        )
                    except Exception as e:
                        fatal_error = e
    if fatal_error is None:
        st.success("Import completed without errors")
    else:
        st.error("Import failed due to a fatal error")
    # Try to display the debug context even if an error occurred
    display_debug_ctx(st.session_state.debug_executor)
    if fatal_error is not None:
        raise fatal_error

elif debug_what == 'Merge':
    debug_app = main_app.copy('tmp')
    fatal_error = None
    with st.container(border=True):
        a = debug_app.app.accounts
        a_info = [ f" - {v.name} ({v.PROVIDER_ID}) - {len(v.data)} rows" for v in a.values() ]
        st.code(f"There are {len(a)} accounts to merge:\n{'\n'.join(a_info)}")
        c1, c2 = st.columns(2)
        if c1.button('Reset', use_container_width=True, key='debug-reset'):
            st.session_state.debug_executor = RecordingExecutor()
        if c2.button('Debug Merge', type='primary', use_container_width=True):
            with st.spinner('Merging...'):
                st.session_state.debug_executor = RecordingExecutor()
                try:
                    debug_app.app.merge_accounts(executor=st.session_state.debug_executor)
                except Exception as e:
                    fatal_error = e
    if fatal_error is None:
        st.success("Merge operation completed without errrors")
    else:
        st.error("Merge operation failed due to a fatal error")
    # Try to display the debug context even if an error occurred
    display_debug_ctx(st.session_state.debug_executor)
    if fatal_error is not None:
        raise fatal_error
