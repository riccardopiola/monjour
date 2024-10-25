from collections import namedtuple
import pandas as pd

from lib.importers.unicredit import Unicredit, UnicreditCategory

def add_currency_info(sheet: Unicredit, df: pd.DataFrame) -> pd.DataFrame:
    new_df = df.assign(currency=sheet.currency)
    return new_df

def add_unicredit_category(sheet: Unicredit, df: pd.DataFrame) -> pd.DataFrame:

    def process_row(row):
        d = row.desc
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
                row['payment_details'] = fields[2]
                row['counterpart'] = fields[3]
                row['location'] = fields[4]
                row['desc'] = ''
            case UnicreditCategory.SEPA_DIRECT_DEBIT:
                row['payment_details'] = fields[2]
                row['counterpart'] = fields[4]
                row['desc'] = fields[3] + fields[5] + fields[6]
            case UnicreditCategory.OUTGOING_TRANSFER \
                | UnicreditCategory.INCOMING_TRANSFER:
                row['payment_details'] = fields[2]
                row['counterpart'] = fields[3]
                row['desc'] = fields[4]
            case _:
                row['desc'] = fields[2:]
        return row

    new_df = df.apply(process_row, axis=1)
    return new_df # type: ignore

UNICREDIT_IT_MODULES = [
    add_currency_info,
    add_unicredit_category
]