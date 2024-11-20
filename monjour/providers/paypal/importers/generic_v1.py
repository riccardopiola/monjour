import pandas as pd
from typing import IO

from monjour.core.account import Account
from monjour.core.importer import importer, Importer, ImportContext
from monjour.core.archive import ArchiveID
from monjour.core.common import DateRange

import monjour.providers.generic.importers.csv_importer as csv_importer
from monjour.providers.paypal.paypal_types import PaypalTransactionType

def combine_date_hour(df: pd.DataFrame, _ctx: ImportContext) -> pd.DataFrame:
    df['date'] = pd.to_datetime(df['paypal_date'] + ' ' + df['paypal_time'])
    return df

paypal_cast_columns = csv_importer.cast_columns({
    'date':                     'datetime64[s]',
    'amount':                   'float64',
    'currency':                 'string',
    'paypal_date':              'datetime64[s]',
    'paypal_time':              'string',
    'paypal_gross':             'float64',
    'paypal_fee':               'float64',
    'paypal_net':               'float64',
    'paypal_transaction_id':    'string',
    'paypal_sender_email':      'string',
    'paypal_bank_name':         'string',
    'paypal_bank_account':      'string',
    'paypal_shipping_and_handling_amount': 'float64',
    'paypal_vat':               'float64',
})

def map_paypal_transaction_type(transaction_type_mapping: dict[str, str]):
    def middleware(df: pd.DataFrame, _ctx: ImportContext) -> pd.DataFrame:
        df['paypal_transaction_type'] = df['paypal_desc']\
            .map(transaction_type_mapping)\
            .fillna(PaypalTransactionType.UNKNOWN.value)
        return df
    return middleware

@importer(v='1.0', locale="*")
class PayPalImporter(Importer):

    def import_file(
        self,
        ctx: ImportContext,
        file: IO[bytes],
    ) -> pd.DataFrame:
        df = pd.read_csv(file)

        # Apply middlewares
        df = csv_importer.add_archive_id(df, ctx)
        df = csv_importer.add_empty_category_column(df, ctx)
        df = csv_importer.create_deterministic_index(df, ctx)
        df = paypal_cast_columns(df, ctx)
        df = csv_importer.remove_useless_columns(df, ctx)

        return df
