from monjour.utils.locale_importer import LocaleImporter
from monjour.core.importer import ImporterInfo

unic_locale_importer = LocaleImporter('UnicreditImporter', 'monjour.providers.unicredit.importers')
unic_locale_importer.add_option(locale='it_IT', v='1.0', module=".it_IT_v1")
