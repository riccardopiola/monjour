import pandas as pd

from monjour.core.importer import *

from monjour.providers.paypal.paypal_types import PaypalTransactionType
import monjour.providers.paypal.importers.generic_v1 as paypal_common
import monjour.providers.generic.importers.csv_importer as csv_importer

COLUMN_MAPPING = {
    'Data':                     'paypal_date',
    'Ora':                      'paypal_time',
    'Fuso orario':              'paypal_timezone',
    'Descrizione':              'paypal_desc',
    'Valuta':                   'currency',
    'Lordo ':                   'paypal_gross',
    'Tariffa ':                 'paypal_fee',
    'Netto':                    'paypal_net',
    'Saldo':                    'amount',
    'Codice transazione':       'paypal_transaction_id',
    'Indirizzo email mittente': 'paypal_sender_email',
    'Nome':                     'paypal_name',
    'Nome banca':               'paypal_bank_name',
    'Conto bancario':           'paypal_bank_account',
    'Importo per spedizione e imballaggio': 'paypal_shipping_and_handling_amount',
    'IVA':                      'paypal_vat',
}

TRANSACTION_TYPE_MAPPING = {
    'Pagamento da cellulare':                       PaypalTransactionType.MOBILE_PAYMENT.value,
    'Bonifico bancario sul conto PayPal':           PaypalTransactionType.BANK_TRANSFER_TO_PAYPAL.value,
    'Pagamento Express Checkout':                   PaypalTransactionType.EXPRESS_CHECKOUT_PAYMENT.value,
    'Blocco saldo per revisione contestazione':     PaypalTransactionType.BALANCE_HOLD_FOR_DISPUTE_REVIEW.value,
    'Annullamento blocco per risoluzione contestazione': PaypalTransactionType.RELEASE_BALANCE_HOLD_RESOLVED.value,
    'Rimborso di pagamento':                        PaypalTransactionType.PAYMENT_REFUND.value,
    'Pagamento preautorizzato utenza':              PaypalTransactionType.PREAUTHORIZED_UTILITY_PAYMENT.value,
    'Pagamento su sito web':                        PaypalTransactionType.WEBSITE_PAYMENT.value,
    'Conversione di valuta generica':               PaypalTransactionType.GENERIC_CURRENCY_CONVERSION.value,
    'Blocco conto per autorizzazione aperta':       PaypalTransactionType.ACCOUNT_HOLD_FOR_AUTHORIZATION.value,
    "Storno di blocco conto generico":              PaypalTransactionType.REVERSAL_OF_GENERIC_ACCOUNT_HOLD.value,
    "Trasferimento avviato dall'utente":            PaypalTransactionType.USER_INITIATED_TRANSFER.value,
}

@importer(v='1.0', locale="it_IT")
class PayPalImporter(csv_importer.CSVImporter):

    csv_args = { 'decimal': ',' }

    csv_transformers = [
        csv_importer.add_archive_id,
        csv_importer.create_deterministic_index,
        csv_importer.rename_columns(COLUMN_MAPPING),
        paypal_common.paypal_cast_columns,
        paypal_common.combine_date_hour,
        paypal_common.map_paypal_transaction_type(TRANSACTION_TYPE_MAPPING),
        csv_importer.remove_useless_columns
    ]

