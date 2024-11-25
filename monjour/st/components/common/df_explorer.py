import pandas as pd
import streamlit as st
from typing import Any, Literal
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from streamlit_extras.mandatory_date_range import date_range_picker

from monjour.st.utils import key_combine

def df_explorer(df: pd.DataFrame, key: str|None = None, case: bool = False) -> pd.DataFrame:
    """
    Mostly copied from streamlit_extras.dataframe_explorer.dataframe_explorer

    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe
        case (bool, optional): If True, text inputs will be case sensitive. Defaults to True.

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    if key is None:
        random_key_base = pd.util.hash_pandas_object(df)
    else:
        random_key_base = key

    with st.container():
        to_filter_columns = st.multiselect(
            "Filter dataframe on",
            df.columns,
            key=f"{random_key_base}_multiselect",
        )
        filters: dict[str, Any] = dict()
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if isinstance(df[column].dtype, pd.CategoricalDtype):
                left.write("↳")
                filters[column] = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                    key=f"{random_key_base}_{column}",
                )
                df = df[df[column].isin(filters[column])]
            elif is_numeric_dtype(df[column]):
                left.write("↳")
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                filters[column] = right.slider(
                    f"Values for {column}",
                    _min,
                    _max,
                    (_min, _max),
                    step=step,
                    key=f"{random_key_base}_{column}",
                )
                df = df[df[column].between(*filters[column])]
            elif is_datetime64_any_dtype(df[column]):
                left.write("↳")
                filters[column] = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                    key=f"{random_key_base}_{column}",
                )
                if len(filters[column]) == 2:
                    filters[column] = tuple(map(pd.to_datetime, filters[column]))
                    start_date, end_date = filters[column]
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                left.write("↳")
                filters[column] = right.text_input(
                    f"Pattern in {column}",
                    key=f"{random_key_base}_{column}",
                )
                if filters[column]:
                    result = df[column].str.contains(filters[column], case=case).fillna(False)
                    # st.dataframe(result)
                    df = df[result]

    return df

DateSelectOptions = Literal['All', 'Last year', 'Last 90 Days', 'Last 30 Days', 'Last Week', 'Custom']
DATE_SELECT_DEFAULT: list[DateSelectOptions] = ['All', 'Last year', 'Last 90 Days', 'Last 30 Days', 'Last Week', 'Custom' ]

def df_date_filter(df: pd.DataFrame, key: str, from_now: bool = False,
    options: list[DateSelectOptions] = DATE_SELECT_DEFAULT, default: DateSelectOptions|None = None,
    use_container_width: bool = True
):
    """
    Filter a DataFrame by date range.
    Args:
        df:         Original dataframe
        key:        Key to use for the widgets
        from_now:   If True, the end date will be the current date. Defaults to False.
        options:    List of options for the date range. Defaults to DATE_SELECT_DEFAULT.
        default:    Default selection. Defaults to None.
    """
    if default is None:
        default = options[0]
    selection = st.segmented_control('Date range', options, key='home_date_range',
                label_visibility='visible', default=default, selection_mode='single')

    end = pd.Timestamp.now() if from_now else df['date'].max()
    if selection == 'All':
        return df
    elif selection == 'Last year':
        start = end - pd.DateOffset(years=1)
    elif selection == 'Last 90 Days':
        start = end - pd.DateOffset(days=90)
    elif selection == 'Last 30 Days':
        start = end - pd.DateOffset(days=30)
    elif selection == 'Last Week':
        start = end - pd.DateOffset(weeks=1)
    elif selection == 'Custom':
        start = end - pd.DateOffset(days=30)
        result = date_range_picker('Select the date range', default_start=start, default_end=end,
            max_date=pd.Timestamp.now(), key=key_combine(key, 'date_range'))
        start = pd.to_datetime(result[0]) # type: ignore
        end = pd.to_datetime(result[1]) # type: ignore
    else:
        # User selected nothing
        st.warning('Select a date range')
        return df.head()

    return df[df['date'] >= start]

