from monjour.utils.locale_importer import LocaleImporter

locale_helper = LocaleImporter("PaypalImporter", 'monjour.providers.paypal.importers')
locale_helper.add_option(locale="*", v="1.0", module=".generic_v1")
locale_helper.add_option(locale="it_IT", v="1.0", module=".it_IT_v1")