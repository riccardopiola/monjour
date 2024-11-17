from monjour.utils.locale_importer import LocaleImporter
from monjour.core.importer import ImporterInfo

pp_locale_importer = LocaleImporter('monjour.providers.paypal.importers')
pp_locale_importer += ImporterInfo(locale="*", v="1.0", cls_name="PaypalImporter", module=".generic")