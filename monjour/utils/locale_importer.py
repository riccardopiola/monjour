from importlib import import_module
from typing import TYPE_CHECKING

from monjour.core.importer import ImporterInfo, Importer

if TYPE_CHECKING:
    from monjour.core.account import Account

class LocaleImporter:
    cls_name: str
    module_base: str
    importers: list[ImporterInfo]
    cache: dict[str, type[Importer]]

    def __init__(self, cls_name: str, module_base: str):
        self.cls_name = cls_name
        self.module_base = module_base
        self.importers = []
        self.cache = {}

    def add_option(self, locale: str, v: str, cls_name: str|None=None, module: str|None=None):
        cls_name = cls_name or self.cls_name
        if module is None:
            module = self.module_base
        elif module.startswith('.'):
            module = self.module_base + module
        else:
            module = module
        self.importers.append(ImporterInfo(locale, v, cls_name, module))

    def filter(self, with_locale: str|None = None, with_version: str|None=None,
               with_name: str|None=None) -> list[ImporterInfo]:
        all = self.importers
        if with_locale is not None:
            all = [i for i in all if i.supports_locale(with_locale)]
        if with_version is not None:
            all = [i for i in all if i.version == with_version]
        if with_name is not None:
            all = [i for i in all if i.friendly_name == with_name]
        return all

    def find_first(self, with_locale: str|None = None, with_version: str|None=None,
                   with_name: str|None=None) -> ImporterInfo:
        results = self.filter(with_locale, with_version, with_name)
        if len(results) == 0:
            raise Exception('No importer found')
        return results[0]

    def load_first(self, with_locale: str|None = None, with_version: str|None=None,
                   with_name: str|None=None) -> type[Importer]:
        results = self.filter(with_locale, with_version, with_name)
        if len(results) == 0:
            raise Exception('No importer found')
        return self.load_importer(results[0])

    def load_importer(self, info: ImporterInfo) -> type[Importer]:
        # First check the cache
        if info.id in self.cache:
            return self.cache[info.id]
        # Load the importer
        module = import_module(info.module)
        importer = getattr(module, info.importer_class_name)
        self.cache[info.id] = importer
        return importer

