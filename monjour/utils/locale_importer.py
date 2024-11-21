from importlib import import_module
from typing import TYPE_CHECKING, TypeVar

from monjour.core.importer import ImporterInfo, Importer

if TYPE_CHECKING:
    from monjour.core.account import Account

class LocaleImporter:
    cls_name: str
    module_base: str
    importers: dict[str, ImporterInfo]
    cache: dict[str, type[Importer]]

    def __init__(self, cls_name: str, module_base: str):
        self.cls_name = cls_name
        self.module_base = module_base
        self.importers = {}
        self.cache = {}

    ##############################################
    # Setup
    ##############################################

    def add_option(self, locale: str, v: str, cls_name: str|None=None, module: str|None=None):
        cls_name = cls_name or self.cls_name
        if module is None:
            module = self.module_base
        elif module.startswith('.'):
            module = self.module_base + module
        else:
            module = module
        info = ImporterInfo(locale, v, cls_name, module)
        self.importers[info.id] = info

    ##############################################
    # Implementation
    ##############################################

    def find(self, with_locale: str|None = None, with_version: str|None=None,
               with_name: str|None=None) -> list[ImporterInfo]:
        all = self.importers.values()
        if with_locale is not None:
            all = [i for i in all if i.supports_locale(with_locale)]
        if with_version is not None:
            all = [i for i in all if i.version == with_version]
        all = sorted(all, key=lambda i: i.version, reverse=True)
        if with_name is not None:
            all = [i for i in all if i.friendly_name == with_name]
        return list(all)

    def load(self, importer_id: str) -> type[Importer]:
        # First check the cache
        if importer_id in self.cache:
            return self.cache[importer_id]
        if (info := self.importers.get(importer_id)) is None:
            raise Exception(f'Importer {importer_id} not found')
        # Load the importer
        module = import_module(info.module)
        importer = getattr(module, info.importer_class_name)
        self.cache[info.id] = importer
        return importer

    ##############################################
    # Convenience
    ##############################################

    def find_first(self, with_locale: str|None = None, with_version: str|None=None,
                   with_name: str|None=None) -> ImporterInfo:
        results = self.find(with_locale, with_version, with_name)
        if len(results) == 0:
            raise Exception('No importer found')
        return results[0]

    def load_first(self, with_locale: str|None = None, with_version: str|None=None,
                   with_name: str|None=None) -> type[Importer]:
        results = self.find(with_locale, with_version, with_name)
        if len(results) == 0:
            raise Exception('No importer found')
        return self.load(results[0].id)


def with_locale_helper(helper_name: str = 'locale_helper', importers_module: str|None=None):
    """
    Mixin for accounts that manager their importers with LocaleImporter. It provides
    implementations for the following abstract methods of Account:
    - get_default_importer
    - get_available_importers
    - set_importer

    Args:
        importers_module:   Module in which to LocaleImporter is defined. If None, it will be assumed
                            to be the module named 'importers' in the same package as the account.
        helper_name:        Name of variable containing the LocaleImporter instance in the module defined
                            by importers_module. Default is 'locale_helper'.
    """
    def mixin(cls):
        module = importers_module or '.'.join([*cls.__module__.split('.')[0:-1], 'importers'])
        locale_importer = getattr(import_module(module), helper_name)
        setattr(cls, '_locale_helper', locale_importer)
        setattr(cls, 'get_default_importer', _get_default_importer)
        setattr(cls, 'get_available_importers', _get_available_importers)
        setattr(cls, 'set_importer', _set_importer)
        return cls
    return mixin

def _get_default_importer(account, locale: str|None=None) -> Importer:
    return account._locale_helper.load_first(with_locale=locale)()

def _get_available_importers(account) -> list[ImporterInfo]:
    return list(account._locale_helper.importers.values())

def _set_importer(account, importer: Importer | str) -> Importer:
    if isinstance(importer, str):
        account._importer = account._locale_helper.load(importer)()
    else:
        account._importer = importer
    return account._importer