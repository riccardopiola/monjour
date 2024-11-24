import pandas as pd
from typing import IO, Any

from monjour.core.archive import DateRange
from monjour.core.importer import Importer, importer, ImportContext
from monjour.core.transaction import Transaction
from monjour.core.transformation import transformer, Transformer

#########################################
# Middlewares
#########################################

@transformer()
def add_archive_id(ctx: ImportContext, df: pd.DataFrame):
    df['archive_id'] = ctx.archive_id
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

@transformer()
def warn_if_empty_dataframe(ctx: ImportContext, df: pd.DataFrame) -> pd.DataFrame:
    if len(df) == 0:
        ctx.diag_warning("Empty DataFrame after applying all transformers")
    return df

@importer(locale="en_US", v='1.0')
class CSVImporter(Importer):
    """
    A generic CSV importer that loads a CSV file into a DataFrame and applies a list of middlewares.
    The CSV file format doesn't have any options. With this architecture, the specific importer that
    inherits from this class (for example PayPalImporter) can be defined in a simple, declarative way.

    Example:
    @importer(locale="*", v='1.0')
    class MyCSVImporter(CSVImporter):
        name = 'my-csv-importer'
        version = '1.0'
        csv_args = {
            'delimiter': ';'
        }
        csv_transformers = [
            rename_columns({
                'Amount': 'amount'
            }),
            cast_columns({
                'amount': 'float64'
            }),
            my_custom_middleware
        ]
    """

    csv_args: dict[str, Any] = {
        'sep': ',',
        'decimal': '.',
        'parse_dates': [ 'date' ],
    }

    csv_transformers: list[Transformer] = [
        add_archive_id,
        create_deterministic_index,
        cast_columns(Transaction.to_pd_dtype_dict()),
        remove_useless_columns,
        warn_if_empty_dataframe
    ]

    def __init__(self, csv_args_overrides: dict[str, str]|None = None):
        super().__init__()
        if csv_args_overrides is not None:
            self.csv_args.update(csv_args_overrides)

    def import_file(
        self,
        ctx: ImportContext,
        file: IO[bytes],
    ) -> pd.DataFrame:
        df = pd.read_csv(file, **self.csv_args)

        block = ctx.executor.new_block((ctx, df))

        for transformer in self.csv_transformers:
            block.exec(transformer)

        return block.last_result

    def try_infer_daterange(
        self,
        file: IO[bytes],
        filename: str | None = None
    ) -> DateRange:
        df = pd.read_csv(file, **self.csv_args, usecols=['date'])
        return DateRange(
            df['date'].min().to_pydatetime(),
            df['date'].max().to_pydatetime()
        )


