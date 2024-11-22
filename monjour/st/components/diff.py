import pandas as pd
import streamlit as st

def show_diff(df1: pd.DataFrame, df2: pd.DataFrame):

    df2_index = None
    if df1.index.name != df2.index.name:
        if df1.index.name is None:
            if 'csv_prev_index' in df2.columns:
                df1.index.name = 'csv_prev_index'
            else:
                st.error("Cannot compare DataFrames with different indexes. Input DF index has no name")
                return
        if df1.index.name in df2.columns:
            df2_index = df2.index.name
            df2 = df2.reset_index()
            df2 = df2.set_index(df1.index.name)
        else:
            st.error("Cannot compare DataFrames with different indexes. Input DF index is not in output DF columns")
            return

    # Detect changes in columns
    added_cols = df2.columns.difference(df1.columns)
    removed_cols = df1.columns.difference(df2.columns)
    common_columns = df1.columns.intersection(df2.columns)

    # Detect row changes
    added_rows = df2.index.difference(df1.index)
    removed_rows = df1.index.difference(df2.index)
    common_rows = df1.index.intersection(df2.index)

    df = pd.merge(df2, df1[removed_cols], how='outer', left_index=True, right_index=True) # type:ignore
    df.loc[removed_rows] = df1.loc[removed_rows] # type:ignore

    aligned_df1 = df1.loc[common_rows, common_columns].reindex(index=common_rows, columns=common_columns)
    aligned_df2 = df2.loc[common_rows, common_columns].reindex(index=common_rows, columns=common_columns)

    changes = aligned_df1 != aligned_df2


    YELLOW = 'background-color: yellow; color: black;'
    RED = 'background-color: red; color: white;'
    GREEN = 'background-color: green; color: white;'
    BLUE = 'background-color: blue; color: white;'

    def apply_style(data: pd.DataFrame):
       # Set the defualt style to empty
        new_df = pd.DataFrame('', index=data.index, columns=data.columns)
        # replace all the True cells in 'changes' with 'background-color: yellow'
        new_df = new_df.mask(changes, YELLOW)
        new_df = new_df.mask(data.isnull(), '')
        new_df.loc[added_rows, :] = GREEN
        new_df[added_cols] = GREEN
        new_df.loc[removed_rows, :] = RED
        new_df[removed_cols] = RED

        if df2_index:
            new_df[df2_index] = BLUE
        return new_df

    styled_df = df.style.apply(apply_style, axis=None)
    st.write('### Output diff')
    # print(styled_df)
    st.dataframe(styled_df)

