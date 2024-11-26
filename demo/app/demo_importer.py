import pandas as pd

from monjour.core.importer import ImportContext, importer
from monjour.core.transformation import transformer

from monjour.providers.generic.importers import csv_importer

@transformer()
def fix_categories(_ctx: ImportContext, df: pd.DataFrame) -> pd.DataFrame:
    df['category'] = df['category'].str.replace('.', '/')
    return df

@importer(v='1.0', locale="*")
class DemoImporter(csv_importer.CSVImporter):

    csv_transformers = [
        csv_importer.add_archive_id,
        csv_importer.create_deterministic_index,
        csv_importer.cast_columns_standard_format,
        fix_categories,
        csv_importer.remove_useless_columns,
        csv_importer.warn_if_empty_dataframe
    ]