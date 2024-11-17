import pandas as pd
from typing import IO, Callable, TypeVar
from functools import wraps

from lib.core.importer import Importer, importer
from lib.core.account import Account
from lib.core.archive import Archive, DateRange, ArchiveID

CsvMiddleware = Callable[[pd.DataFrame, Account, Archive, ArchiveID], pd.DataFrame]

@importer(name='csv-importer', version='1.0')
class CSVImporter(Importer):
    """
    A generic CSV importer that loads a CSV file into a DataFrame and applies a list of middlewares.
    The CSV file format doesn't have any options. With this architecture, the specific importer that
    inherits from this class (for example PayPalImporter) can be defined in a simple, declarative way.

    Example:
    class MyCSVImporter(CSVImporter):
        name = 'my-csv-importer'
        version = '1.0'
        csv_args = {
            'delimiter': ';'
        }
        csv_import_middlewares = [
            rename_columns({
                'Amount': 'amount'
            }),
            cast_columns({
                'amount': 'float64'
            }),
            my_custom_middleware
        ]

    CSV Middlewares are functions that take the Account and the imported Dataframe as arguments, perform
    some operations on the DataFrame and return the modified DataFrame to be passed to the next middleware.
    """

    def import_file(
        self,
        archive_id: ArchiveID,
        file: IO[bytes],
        date_range: DateRange|None=None
    ) -> pd.DataFrame:
        df = pd.read_csv(file)

        df = add_archive_id(df, archive_id)
        df = add_empty_category_column(df)
        df = create_deterministic_index(df, archive_id)
        df = remove_useless_columns(df, self.account)

        return df

#########################################
# Middlewares
#########################################

def add_archive_id(df: pd.DataFrame, archive_id: ArchiveID):
    df['archive_id'] = archive_id
    return df

def add_empty_category_column(df: pd.DataFrame):
    df['category'] = None
    return df

def create_deterministic_index(df: pd.DataFrame, archive_id: ArchiveID):
    df['deterministic_index'] = [f"{archive_id}_{i}" for i in df.index]
    df['deterministic_index'] = df['deterministic_index'].astype('string')
    df.set_index('deterministic_index', inplace=True)
    return df

def rename_columns(column_remapping: dict[str, str]):
    """
    Factory function that returns a CSV middleware that renames columns in the DataFrame
    """
    def middleware(df: pd.DataFrame) -> pd.DataFrame:
        df.rename(columns=column_remapping, inplace=True)
        return df
    return middleware

def cast_columns(column_dtypes: dict, fill_unavailable_cols: bool = False):
    """
    Factory function that returns a CSV middleware that casts columns to the specified dtypes
    """
    def middleware(df: pd.DataFrame) -> pd.DataFrame:
        # cast existing column to their specified dtypes
        for column, dtype in column_dtypes.items():
            if column in df.columns:
                df[column] = df[column].astype(dtype)
            # fill unavailable columns with empty series
            elif fill_unavailable_cols:
                df[column] = pd.Series([], dtype=dtype)
        return df
    return middleware

def remove_useless_columns(df: pd.DataFrame, account: Account) -> pd.DataFrame:
    """
    CSV middleware that removes columns that are not used by the account.

    The columns to keep are defined in the account's DF_COLUMNS attribute.
    """
    useful_columns = account.DF_COLUMNS.keys()
    return df[useful_columns]

