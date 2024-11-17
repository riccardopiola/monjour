from monjour.core.archive import Archive
from monjour.core.account import Account
from monjour.core.importer import Importer

def get_importer_for_locale(account: Account, locale: str|None) -> Importer:
    """
    Try to automatically select an importer based on the locale.
    This function should be overridden by subclasses that can automatically select an importer.
    """
    match locale:
        case 'it_IT':
            from monjour.providers.unicredit.importers.it_IT import UnicreditImporter
            return UnicreditImporter(account)
        case _:
            raise Exception(f'Account "{account.id}" does not have an importer defined and no importer can be selected automatically')