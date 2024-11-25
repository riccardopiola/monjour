import pandas as pd

from monjour.core.account import Account
from monjour.core.importer import Importer
from monjour.utils.locale_importer import with_locale_helper

from monjour.providers.paypal.paypal_types import PaypalTransactionType, PaypalTransaction

@with_locale_helper()
class PayPal(Account):
    PROVIDER_ID = 'paypal'
    TRANSACTION_TYPE = PaypalTransaction

    def __init__(
        self,
        id: str,
        importer: Importer|None = None,
        name: str|None = None,
        locale: str|None = None,
    ):
        super().__init__(id, name=name, importer=importer, locale=locale)