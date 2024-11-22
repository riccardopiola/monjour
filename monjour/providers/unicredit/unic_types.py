import pandas as pd
from enum import Enum
from dataclasses import dataclass
from typing import Literal, TypedDict

from monjour.core.transaction import Transaction, PaymentType

class UnicreditCategory(Enum):
    UNKNOWN             = 'Unknown'             # 'Original: N/A'
    # Fees
    INTEREST_FEES       = 'Interest/Fees'       # 'COMPETENZE (INTERESSI/ONERI)'
    COMMISSIONS_FEES    = 'Commissions/Fees'    # 'COMMISSIONI - PROVVIGIONI - SPESE'
    FIXED_MONTHLY_COST  = 'Fixed Monthly Cost'  # 'MY GENIUS COSTO FISSO MESE'
    TAXES               = 'Taxes'               # 'IMPOSTA BOLLO CONTO CORRENTE DPR642/72-DM24/5/2012'

    # Payments
    PAYMENT             = 'Payment'             # 'PAGAMENTO' or 'PAGAMENTO GOOGLE PAY NFC'
    OTHER_PAYMENTS      = 'Other Payments'      # 'PAGAMENTI DIVERSI'
    OUTGOING_TRANSFER   = 'Outgoing Transfer'   # 'DISPOSIZIONE DI BONIFICO'
    SEPA_DIRECT_DEBIT   = 'SEPA Direct Debit'   # 'ADDEBITO SEPA DD PER FATTURA A VOSTRO CARICO'
    ECOMMERCE           = 'ECommerce'           # 'PAGAMENTO E-Commerce' or 'PAGAMENTO GOOGLE PAY E-Commerce
    PHONE_RECHARGE      = 'Phone Recharge'      # 'RICARICA TELEFONICA SERVIZIO INTERNET BANKING'
    INSURANCE_PREMIUM   = 'Insurance Premium'   # 'PAGAMENTO PREMIO ASSICURAZIONE'

    # Income
    INCOMING_TRANSFER   = 'Incoming Transfer'   # 'BONIFICO A VOSTRO FAVORE'
    ACCOUNT_RECHARGE    = 'Account Recharge'    # 'RICARICA CONTO'
    MISC_CREDITS        = 'Miscellaneous Credits'  # 'ACCREDITI VARI'

@dataclass
class UnicreditTransaction(Transaction):
    # Date in which the transaction was registered
    unicredit_registration_date: pd.Timestamp

    # Unicredit specific identifier of the transaction (dont't rely on this being unique)
    unicredit_id: str

    # Unicredit specific category of the transaction
    unicredit_category: UnicreditCategory

    # The original description
    unicredit_original_desc: str

    unicredit_original_date: pd.Timestamp

# class UnicreditPayment(UnicreditTransaction):
#     unicredit_category: UnicreditCategory.PAYMENT|UnicreditCategory.ECOMMERCE
#     payment_type: PaymentType.CardPayment|PaymentType.Ecommerce
#     payment_type_details: dict[Literal[
#         'card',
#         'provider',
#     ], str|None]
#     extra: dict[Literal[
#         'original_date'
#         'original_amount'
#         'original_currency'
#     ], str|None]
    