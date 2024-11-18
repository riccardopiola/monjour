from monjour.utils.locale_importer import LocaleImporter

pp_locale_importer = LocaleImporter("PaypalImporter", 'monjour.providers.paypal.importers')
pp_locale_importer.add_option(locale="*", v="1.0", module=".generic_v1")
pp_locale_importer.add_option(locale="it_IT", v="1.0", module=".it_IT_v1")