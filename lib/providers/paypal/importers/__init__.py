from lib.core.archive import Archive
from lib.core.account import Account
from lib.core.importer import Importer

def get_importer_for_locale(account: Account, archive: Archive, locale: str) -> Importer:
    """
    Try to automatically select an importer based on the locale.
    This function should be overridden by subclasses that can automatically select an importer.
    """
    match locale:
        case 'it_IT':
            from lib.providers.paypal.importers.it_IT import PayPalImporter
            return PayPalImporter(archive, account)
        case _:
            raise Exception(f'Account "{account.id}" does not have an importer defined and no importer can be selected automatically')