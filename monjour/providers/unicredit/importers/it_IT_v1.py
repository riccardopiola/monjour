import re
import json

from monjour.core.importer import *
from monjour.core.transaction import PaymentType
from monjour.core.transformation import transformer
from monjour.utils.regex_parser import RegexParser

import monjour.providers.generic.importers.csv_importer as csv_importer
from monjour.providers.unicredit.unic_types import UnicreditCategory, UnicreditTransaction
from monjour.providers.unicredit.unic_account import Unicredit

PARSER = RegexParser[UnicreditCategory]()

PARSER.define_class('unic_id', r"\d{15}\,\d{6}")
PARSER.define_class('ecommerce', r"E-Commerce")
PARSER.define_class('date', r"\d{2}/\d{2}/\d{4}")
PARSER.define_class('card', r"\d{4}")
# Matches anything except 3 consecutive spaces
PARSER.define_class('str', r"[^\s]+(?:\s\s?[^\s]+)*")

def _unic_common(*patterns, allow_extras=False):
    pattern = r'\s\s\s+'.join([' {unic_id}', *patterns])
    if allow_extras:
        pattern += '.*'
    return pattern

#####################################
# Fees
#####################################
PARSER.add_case(UnicreditCategory.INTEREST_FEES, _unic_common(
    r"COMPETENZE \(INTERESSI/ONERI\)", allow_extras=True))

PARSER.add_case(UnicreditCategory.COMMISSIONS_FEES, _unic_common(
    r"COMMISSIONI - PROVVIGIONI - SPESE", allow_extras=True))

PARSER.add_case(UnicreditCategory.FIXED_MONTHLY_COST, _unic_common(
    r"MY GENIUS  COSTO FISSO MESE DI {month:str}", allow_extras=True))

PARSER.add_case(UnicreditCategory.TAXES, _unic_common(
    r"IMPOSTA", allow_extras=True))

#####################################
# Payments
#####################################
PARSER.add_case(UnicreditCategory.INSURANCE_PREMIUM,
    _unic_common(r"PAGAMENTO PREMIO ASSICURAZIONE", allow_extras=True))

PARSER.add_case(UnicreditCategory.PAYMENT, _unic_common(
    r"PAGAMENTO {ecommerce}?{payment_provider:str}?\s*del {original_date:date}", # e.g PAGAMENTO E-Commerce del 04/12/2019
    r"CARTA \*{card}", "DI {currency:str}", "{amount:str}", # e.g CARTA *1423    DI EUR            3,00
    "{counterpart:str}", "{location:str}")) # MCDONALD'S MILANO SAN BAB          MILANO

PARSER.add_case(UnicreditCategory.SEPA_DIRECT_DEBIT, _unic_common(
    r"ADDEBITO SEPA DD PER FATTURA A VOSTRO CARICO", # TODO: Figure out what those unknown fields are
    r"{unknown1:str}", "{unknown2:str}", "{counterpart:str}", allow_extras=True))

PARSER.add_case(UnicreditCategory.OTHER_PAYMENTS, _unic_common(
    r"PAGAMENTI DIVERSI", allow_extras=True))

PARSER.add_case(UnicreditCategory.OUTGOING_TRANSFER, _unic_common(
    r"DISPOSIZIONE DI BONIFICO", allow_extras=True))

PARSER.add_case(UnicreditCategory.PHONE_RECHARGE, _unic_common(
    r"RICARICA TELEFONICA SERVIZIO INTERNET BANKING", allow_extras=True))
#####################################
# Income
#####################################
PARSER.add_case(UnicreditCategory.INCOMING_TRANSFER, _unic_common(
    r"BONIFICO A VOSTRO FAVORE .*DA\s+{counterpart:str}.+PER\s+{subject:str}" +
    r".*TRN\s+{trn:str}.*(?:VA\s+{iban:str})?", allow_extras=True))

PARSER.add_case(UnicreditCategory.ACCOUNT_RECHARGE, _unic_common(
    r"RICARICA CONTO", allow_extras=True))

PARSER.add_case(UnicreditCategory.MISC_CREDITS, _unic_common(
    r"ACCREDITI VARI", allow_extras=True))

PARSER.add_case(UnicreditCategory.UNKNOWN, r" {unic_id}.*")

#####################################
# Middlewares
#####################################

@transformer()
def add_unicredit_category(ctx: ImportContext, df: pd.DataFrame) -> pd.DataFrame:
    PARSER.build()
    def process_row(row):
        # Limit multiple spaces to three
        desc = re.sub(r'\s\s\s+', '   ', row['unicredit_original_desc'])
        result = PARSER.parse(desc)
        if result is None:
            # The regex match for UnicreidtCategory.UNKNOWN is very permissive. If we reach this point
            # it means the file is not of the correct format or it is malformed
            raise ValueError(f'Invalid Unicredit transaction: (csv_row: {row['csv_prev_index']}) {desc}')
        category, values = result
        row['unicredit_id'] = values['unic_id']
        row['unicredit_category'] = category.value
        row['unicredit_original_desc'] = desc[23:] # Description without unicredit_id
        match category:
            case UnicreditCategory.FIXED_MONTHLY_COST:
                row['desc'] = f"Unicredit monthly cost for {values['month']}"
            case UnicreditCategory.PAYMENT:
                if values['ecommerce'] is not None:
                    row['payment_type'] = PaymentType.Ecommerce.value
                    row['unicredit_category'] = UnicreditCategory.ECOMMERCE.value
                else:
                    row['payment_type'] = PaymentType.CardPayment.value
                row['payment_type_details'] = json.dumps({
                    'card': values['card'],
                    'provider': values['payment_provider'], # maybe move this to extras
                })
                row['extra'] = json.dumps({
                    'original_amount': values['amount'],
                    'original_currency': values['currency']
                })
                row['counterpart'] = values['counterpart']
                row['location'] = values['location']
                row['unicredit_original_date'] = values['original_date']
            case UnicreditCategory.SEPA_DIRECT_DEBIT:
                row['payment_type'] = PaymentType.PreauthorizedDebit.value
                row['counterpart'] = values['counterpart']
            case UnicreditCategory.OUTGOING_TRANSFER:
                row['payment_type'] = PaymentType.Transfer.value
                row['desc'] = "Outgoing transfer"
            case UnicreditCategory.INCOMING_TRANSFER:
                row['payment_type'] = PaymentType.Transfer.value
                row['counterpart'] = values['counterpart']
                row['desc'] = "Incoming transfer from " + values['counterpart']
            case UnicreditCategory.UNKNOWN:
                ctx.diag_debug(f'Unknown transaction: {row['date']} {row['amount']} {row['unicredit_original_desc']}')
            case _:
                row['desc'] = row['unicredit_original_desc']
        return row

    new_df = df.apply(process_row, axis=1)
    return new_df # type: ignore

@transformer()
def add_currency_info(ctx: ImportContext, df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a new column 'currency' in the dataframe with the currency of the sheet
    """
    if not isinstance(ctx.account, Unicredit):
        raise ValueError(f'Expected account type Unicredit, got {type(ctx.account).__name__}')
    df['currency'] = ctx.account.currency
    return df

#####################################
# Importer
#####################################

UNICREDIT_IT_COLUMN_MAPPING = {
    'Data Registrazione':   'unicredit_registration_date',
    'Data valuta':          'date',
    'Descrizione':          'unicredit_original_desc',
    'Importo (EUR)':        'amount',
}

UNICREDIT_IT_COLUMN_DTYPES = UnicreditTransaction.to_pd_dtype_dict()

@importer(locale='it_IT', v='1.0')
class UnicreditImporter(csv_importer.CSVImporter):

    csv_args = {
        'sep': ';',
        'decimal': ',',
        'thousands': '.',
        'parse_dates': ['Data Registrazione', 'Data valuta'],
        'dayfirst': True
    }

    csv_transformers = [
        csv_importer.add_archive_id,
        csv_importer.add_empty_category_column,
        csv_importer.create_deterministic_index,
        csv_importer.rename_columns(UNICREDIT_IT_COLUMN_MAPPING),
        csv_importer.cast_columns(UNICREDIT_IT_COLUMN_DTYPES),
        add_currency_info,
        add_unicredit_category,
        csv_importer.remove_useless_columns
    ]

    def try_infer_daterange(
        self,
        file: IO[bytes],
        filename: str|None=None,
    ) -> DateRange:
        df = pd.read_csv(file, **self.csv_args)
        if 'Data valuta' not in df.columns:
            raise ValueError('Failed to infer date range: "Data valuta" column not found')
        return DateRange(
            df['Data valuta'].min().to_pydatetime(),
            df['Data valuta'].max().to_pydatetime()
        )