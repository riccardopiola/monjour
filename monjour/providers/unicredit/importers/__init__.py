from monjour.utils.locale_importer import LocaleImporter
from monjour.core.importer import ImporterInfo

unic_locale_importer = LocaleImporter('monjour.providers.unicredit.importers')
unic_locale_importer += ImporterInfo(locale='it_IT', v='1.0', cls_name='UnicreditImporter')
