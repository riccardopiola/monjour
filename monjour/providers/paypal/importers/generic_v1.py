import pandas as pd
from typing import IO

from monjour.core.account import Account
from monjour.core.importer import importer, Importer, ImportContext
from monjour.core.archive import ArchiveID
from monjour.core.common import DateRange
from monjour.core.transformation import Transformer, transformer

import monjour.providers.generic.importers.csv_importer as csv_importer
from monjour.providers.paypal.paypal_types import PaypalTransactionType, PaypalTransaction

@transformer()
def combine_date_hour(_ctx: ImportContext, df: pd.DataFrame) -> pd.DataFrame:
    df['date'] = pd.to_datetime(df['paypal_date'] + ' ' + df['paypal_time'])
    return df

paypal_cast_columns = csv_importer.cast_columns(PaypalTransaction.to_pd_dtype_dict())

def map_paypal_transaction_type(transaction_type_mapping: dict[str, str]):
    def transformer(ctx: ImportContext, df: pd.DataFrame) -> pd.DataFrame:
        df['paypal_transaction_type'] = df['paypal_desc']\
            .map(transaction_type_mapping)\
            .fillna(PaypalTransactionType.UNKNOWN.value)
        return df
    return Transformer(transformer, 'map_paypal_transaction_type', transaction_type_mapping=transaction_type_mapping)

@importer(v='1.0', locale="*")
class PayPalImporter(csv_importer.CSVImporter):

    csv_args = {}

    csv_transformers = [
        csv_importer.add_archive_id,
        csv_importer.create_deterministic_index,
        combine_date_hour,
        paypal_cast_columns,
        csv_importer.remove_useless_columns,
    ]
