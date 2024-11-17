from importlib import import_module
from typing import TYPE_CHECKING

from monjour.core.importer import ImporterInfo, Importer

if TYPE_CHECKING:
    from monjour.core.account import Account

class LocaleImporter:
    import_module_base: str
    importers: list[ImporterInfo]
    cache: dict[str, type[Importer]]

    def __init__(self, import_module_base: str):
        self.import_module_base = import_module_base
        self.importers = []
        self.cache = {}

    def __iadd__(self, other: ImporterInfo):
        self.importers.append(other)
        return self

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
                   with_name: str|None=None) -> Importer:
        results = self.filter(with_locale, with_version, with_name)
        if len(results) == 0:
            raise Exception('No importer found')
        return self.load_importer(results[0])

    def load_first(self, with_locale: str|None = None, with_version: str|None=None,
                   with_name: str|None=None) -> type[Importer]:
        results = self.filter(with_locale, with_version, with_name)
        if len(results) == 0:
            raise Exception('No importer found')
        return self.load_importer(results[0])

    def load_importer(self, info: ImporterInfo) -> type[Importer]:
        if info.id in self.cache:
            return self.cache[info.id]
        if info.module is None:
            module_name = self.import_module_base + "." + info.supported_locale
        elif info.module.startswith('.'):
            module_name = self.import_module_base + info.module
        else:
            module_name = info.module
        module = import_module(module_name)
        importer = getattr(module, info.importer_class_name)
        self.cache[info.id] = importer
        return importer

