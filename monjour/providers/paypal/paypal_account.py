import pandas as pd

from monjour.core.account import Account
from monjour.core.importer import Importer

from monjour.providers.paypal.paypal_types import PaypalTransactionType

class PayPal(Account):
    PROVIDER_ID = 'paypal'

    DF_COLUMNS = Account.DF_COLUMNS | {
        'paypal_transaction_id':    pd.Series([], dtype='string'),
        'paypal_sender_email':      pd.Series([], dtype='string'),
        'paypal_transaction_type':  pd.Categorical([], categories=[c.value for c in PaypalTransactionType]),
    }

    def __init__(
        self,
        id: str,
        importer: Importer|None = None,
        name: str|None = None,
        locale: str|None = None,
    ):
        super().__init__(id, name=name, importer=importer, locale=locale)
