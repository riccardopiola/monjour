import pandas as pd
from typing import IO, Any

from monjour.core.importer import Importer, importer, ImportContext
from monjour.core.transformation import transformer, Transformer

#########################################
# Middlewares
#########################################

@transformer()
def add_archive_id(ctx: ImportContext, df: pd.DataFrame):
    df['archive_id'] = ctx.archive_id
    return df

@transformer()
def add_empty_category_column(ctx: ImportContext, df: pd.DataFrame):
    df['category'] = None
    return df

@transformer()
def create_deterministic_index(ctx: ImportContext, df: pd.DataFrame):
    # Save the old index in a new column
    df['csv_prev_index'] = df.index
    # Create a new deterministic index
    df['deterministic_index'] = [f"{ctx.archive_id}_{i}" for i in df.index]
    df['deterministic_index'] = df['deterministic_index'].astype('string')
    df.set_index('deterministic_index', inplace=True)
    return df

def rename_columns(column_remapping: dict[str, str]):
    def transformer(ctx: ImportContext, df: pd.DataFrame) -> pd.DataFrame:
        df.rename(columns=column_remapping, inplace=True)
        return df
    return Transformer(transformer, 'csv_importer.rename_columns', column_remapping=column_remapping)

def cast_columns(column_dtypes: dict[str, Any], fill_unavailable_cols: bool = True):
    def transformer(ctx: ImportContext, df: pd.DataFrame) -> pd.DataFrame:
        for column, dtype in column_dtypes.items():
            if column in df.columns:
                df[column] = df[column].astype(dtype)
            # fill unavailable columns with empty series
            elif fill_unavailable_cols:
                df[column] = None
                df[column].astype(dtype)
        return df
    return Transformer(transformer, 'csv_importer.cast_columns', column_dtypes=column_dtypes, fill_unavailable_cols=fill_unavailable_cols)

@transformer()
def remove_useless_columns(ctx: ImportContext, df: pd.DataFrame) -> pd.DataFrame:
    """
    CSV middleware that removes columns that are not used by the account.

    The columns to keep are defined in the account's DF_COLUMNS attribute.
    """
    useful_columns = ctx.account.TRANSACTION_TYPE.get_attribute_names()
    return df[useful_columns]


@importer(locale="*", v='1.0')
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
        csv_import_transformers = [
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

    csv_args: dict[str, Any] = {}

    csv_transformers: list[Transformer] = [
        add_archive_id,
        add_empty_category_column,
        create_deterministic_index,
        remove_useless_columns
    ]

    def import_file(
        self,
        ctx: ImportContext,
        file: IO[bytes],
    ) -> pd.DataFrame|None:
        df = pd.read_csv(file, **self.csv_args)

        block = ctx.executor.enter(self.info.id, (ctx, df))

        for transformer in self.csv_transformers:
            block.enqueue(transformer)

        return ctx.executor.run()

