import pandas as pd

def df_drop_empty_columns(df, enable=True):
    if not enable:
        return df
    return df.dropna(axis=1, how='all')

def df_show_first(df, n:int|None=None, enable=True):
    if not enable:
        return df
    return df.head(n)


    
