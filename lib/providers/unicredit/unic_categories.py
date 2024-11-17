from enum import Enum

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