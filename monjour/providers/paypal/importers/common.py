import pandas as pd
from typing import IO

from monjour.core.account import Account
from monjour.core.importer import importer, Importer
from monjour.core.archive import ArchiveID
from monjour.core.common import DateRange

import monjour.providers.generic.csv_importer as csv_importer
from monjour.providers.paypal.paypal_types import PaypalTransactionType

def combine_date_hour(df: pd.DataFrame) -> pd.DataFrame:
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
    def middleware(df: pd.DataFrame) -> pd.DataFrame:
        df['paypal_transaction_type'] = df['paypal_desc']\
            .map(transaction_type_mapping)\
            .fillna(PaypalTransactionType.UNKNOWN.value)
        return df
    return middleware

@importer(name='paypal-generic', version='1.0')
class PayPalImporter(Importer):

    def import_file(
        self,
        archive_id: ArchiveID,
        file: IO[bytes],
        date_range: DateRange|None=None
    ) -> pd.DataFrame:
        df = pd.read_csv(file)

        # Apply middlewares
        df = csv_importer.add_archive_id(df, archive_id)
        df = csv_importer.add_empty_category_column(df)
        df = csv_importer.create_deterministic_index(df, archive_id)
        df = paypal_cast_columns(df)

        return df
