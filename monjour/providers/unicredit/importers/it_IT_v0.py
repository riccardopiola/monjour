import pandas as pd
from datetime import datetime

import monjour.core.log as log
from monjour.core.importer import *

import monjour.providers.generic.importers.csv_importer as csv_importer
from monjour.providers.unicredit.unic_types import UnicreditCategory
from monjour.providers.unicredit.unic_account import Unicredit

def add_currency_info(df: pd.DataFrame, ctx: ImportContext) -> pd.DataFrame:
    """
    Create a new column 'currency' in the dataframe with the currency of the sheet
    """
    if not isinstance(ctx.account, Unicredit):
        raise ValueError(f'Expected account type Unicredit, got {type(ctx.account).__name__}')
    df['currency'] = ctx.account.currency
    return df

def add_unicredit_category(df: pd.DataFrame, _ctx: ImportContext) -> pd.DataFrame:

    def process_row(row):
        d = row['unicredit_desc']
        fields = []
        for i in range(0, len(d), 50):
            desc_slice = d[i:i+50]
            if d[i-1] != ' ' and d[i] == ' ' and i > 0:
                fields[-1] += desc_slice
            else:
                fields.append(desc_slice.strip())
        # TODO: match transaction
        row['unicredit_id'] = fields[0]
        row['unicredit_original_desc'] = ' '.join(fields[1:])

        # Fees
        f = fields[1]
        if f.startswith('COMPETENZE (INTERESSI/ONERI)'):
            unic_category = UnicreditCategory.INTEREST_FEES
        elif f.startswith('COMMISSIONI - PROVVIGIONI - SPESE'):
            unic_category = UnicreditCategory.COMMISSIONS_FEES
        elif f.startswith('MY GENIUS COSTO FISSO MESE'):
            unic_category = UnicreditCategory.FIXED_MONTHLY_COST

        # Taxes
        elif f.startswith('IMPOSTA BOLLO CONTO CORRENTE DPR642/72-DM24/5/2012'):
            unic_category = UnicreditCategory.TAXES

        # Payments
        elif f.startswith('PAGAMENTO E-Commerce') or \
            f.startswith('PAGAMENTO GOOGLE PAY E-Commerce'):
            unic_category = UnicreditCategory.ECOMMERCE

        elif f.startswith('PAGAMENTO PREMIO ASSICURAZIONE'):
            unic_category = UnicreditCategory.INSURANCE_PREMIUM

        elif f.startswith('PAGAMENTO GOOGLE PAY NFC') or \
            f.startswith('PAGAMENTO') or \
            f.startswith('PAGAMENTO Contactless'):
            unic_category = UnicreditCategory.PAYMENT

        elif f.startswith('ADDEBITO SEPA DD PER FATTURA A VOSTRO CARICO'):
            unic_category = UnicreditCategory.SEPA_DIRECT_DEBIT
        elif f.startswith('PAGAMENTI DIVERSI'):
            unic_category = UnicreditCategory.OTHER_PAYMENTS

        elif f.startswith('DISPOSIZIONE DI BONIFICO'):
            unic_category = UnicreditCategory.OUTGOING_TRANSFER

        elif f.startswith('RICARICA TELEFONICA SERVIZIO INTERNET BANKING'):
            unic_category = UnicreditCategory.PHONE_RECHARGE

        # Income
        elif f.startswith('BONIFICO A VOSTRO FAVORE'):
            unic_category = UnicreditCategory.INCOMING_TRANSFER

        elif f.startswith('RICARICA CONTO'):
            unic_category = UnicreditCategory.ACCOUNT_RECHARGE

        elif f.startswith('ACCREDITI VARI'):
            unic_category = UnicreditCategory.MISC_CREDITS

        # Unknown
        else:
            unic_category = UnicreditCategory.UNKNOWN

        row['unicredit_category'] = unic_category.value
        match unic_category:
            case UnicreditCategory.PAYMENT \
                | UnicreditCategory.ECOMMERCE:
                if len(fields) < 5:
                    row['unicredit_category'] = UnicreditCategory.UNKNOWN.value
                    row['desc'] = ' '.join(fields[2:])
                    log.warning(f'Unknown payment: {row}')
                else:
                    row['payment_details'] = fields[2]
                    row['counterpart'] = fields[3]
                    row['location'] = fields[4]
                    row['desc'] = ''
            case UnicreditCategory.SEPA_DIRECT_DEBIT:
                if len(fields) < 7:
                    row['unicredit_category'] = UnicreditCategory.UNKNOWN.value
                    row['desc'] = ' '.join(fields[2:])
                    log.warning(f'Unknown SEPA direct debit: {row}')
                else:
                    row['payment_details'] = fields[2]
                    row['counterpart'] = fields[4]
                    row['desc'] = fields[3] + fields[5] + fields[6]
            case UnicreditCategory.OUTGOING_TRANSFER \
                | UnicreditCategory.INCOMING_TRANSFER:
                if len(fields) < 5:
                    row['unicredit_category'] = UnicreditCategory.UNKNOWN.value
                    row['desc'] = ' '.join(fields[2:])
                    log.warning(f'Unknown transfer: {row}')
                else:
                    row['payment_details'] = fields[2]
                    row['counterpart'] = fields[3]
                    row['desc'] = fields[4]
            case _:
                row['desc'] = ' '.join(fields[2:])
        return row

    new_df = df.apply(process_row, axis=1)
    return new_df # type: ignore


UNICREDIT_IT_COLUMN_MAPPING = {
    'Data Registrazione':   'unicredit_registration_date',
    'Data valuta':          'date',
    'Descrizione':          'unicredit_desc',
    'Importo (EUR)':        'amount',
}

UNICREDIT_IT_COLUMN_DTYPES = {
    'date':                 'datetime64[s]',
    'amount':               'float64',
    'unicredit_registration_date':    'datetime64[s]',
    'unicredit_desc':       'string',
}

@importer(locale='it_IT', v='1.0')
class UnicreditImporter(Importer):

    def import_file(
        self,
        ctx: ImportContext,
        file: IO[bytes],
    ) -> pd.DataFrame:
        df = pd.read_csv(file, sep=';', decimal=',', thousands='.',
            parse_dates=['Data Registrazione', 'Data valuta'], dayfirst=True)

        df = csv_importer.add_archive_id(df, ctx)
        df = csv_importer.add_empty_category_column(df, ctx)
        df = csv_importer.create_deterministic_index(df, ctx)
        df = csv_importer.rename_columns(UNICREDIT_IT_COLUMN_MAPPING)(df, ctx)
        df = csv_importer.cast_columns(UNICREDIT_IT_COLUMN_DTYPES)(df, ctx)
        df = add_currency_info(df, ctx)
        df = add_unicredit_category(df, ctx)
        df = csv_importer.remove_useless_columns(df, ctx)

        return df

    def try_infer_daterange(
        self,
        file: IO[bytes],
        filename: str|None=None,
    ) -> DateRange | None:
        df = pd.read_csv(file, sep=';', decimal=',', thousands='.', usecols=['Data valuta'],
            parse_dates=['Data valuta'], dayfirst=True)
        if 'Data valuta' not in df.columns:
            return None
        return DateRange(
            df['Data valuta'].min().to_pydatetime(),
            df['Data valuta'].max().to_pydatetime()
        )