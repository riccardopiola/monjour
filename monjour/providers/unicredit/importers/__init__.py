from monjour.utils.locale_importer import LocaleImporter
from monjour.core.importer import ImporterInfo

locale_helper = LocaleImporter('UnicreditImporter', 'monjour.providers.unicredit.importers')
locale_helper.add_option(locale='it_IT', v='1.0', module=".it_IT_v1")
