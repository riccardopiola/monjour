import streamlit as st
import datetime as dt
from dataclasses import dataclass
from typing import IO

from streamlit_extras.mandatory_date_range import date_range_picker

import monjour.core.log as log
from monjour.core.common import DateRange
from monjour.core.account import Account
from monjour.core.importer import ImporterInfo, Importer

from monjour.st import StApp
from monjour.st.utils import key_combine


@st.fragment
def account_selector(st_app: StApp, key_base:str) -> str:
    # Create a dropdown menu
    accounts = st_app.app.accounts

    return st.selectbox('Account', [account.id for account in accounts.values()], key=key_combine(key_base, 'account_select'),
        format_func=lambda id: f"{accounts[id].id} [{accounts[id].PROVIDER_ID}]")

@st.fragment
def importer_selector(st_app: StApp, account_id: str, key_base: str) -> ImporterInfo:
    # Importer selection
    account = st_app.app.accounts[account_id]
    importers = st_app.list_all_importers()
    all_importers = sorted(importers[account_id], key=lambda imp: imp.id == account.importer.info.id, reverse=True)
    importer_info = st.selectbox('Importer', all_importers, key=key_combine(key_base, 'importer_select'),
                        format_func=lambda imp: imp.id)
    return importer_info

@dataclass
class FileImportOptions:
    account: Account
    importer: Importer
    date_range: DateRange
    file: IO[bytes]

def file_import_options(st_app: StApp, page: str):
    (c1, c2) = st.columns(2)
    with c1:
        account_id = account_selector(st_app, page)
    with c2:
        importer_info = importer_selector(st_app, account_id, page)

    account = st_app.app.accounts[account_id]
    importer = account.set_importer(importer_info.id)

    if file := st.file_uploader('File', key=key_combine(page, 'import_file_upload')):
        # TODO: Check if the importer can handle the file

        # Try to infer date range from the file
        inferred_end = dt.datetime.now()
        inferred_start = inferred_end - dt.timedelta(days=30)
        try:
            if (date_range := importer.try_infer_daterange(file, file.name)) is not None:
                inferred_start = date_range.start
                inferred_end = date_range.end
                st.info(f"""The date range was inferred automatically. Adjust it if necessary.""")
        except NotImplementedError:
            st.info(f"""The selected importer does not support inferring the date range from the filename.
            Please select the date range manually.""")
        except Exception as e:
            msg = f"Error while trying to automatically infer date range: {e}"
            st.warning(msg)
            log.warning(msg)
        finally:
            file.seek(0)

        # Date range selection controls return a tuple of two datetime objects
        date_range = date_range_picker('Date range',
            default_start=inferred_start, default_end=inferred_end,
            key=key_combine(page, 'date_range_select')
        )

        return FileImportOptions(
            account=account,
            importer=importer,
            date_range=DateRange(
                dt.datetime.combine(date_range[0], dt.time.min), # type: ignore
                dt.datetime.combine(date_range[1], dt.time.max) # type: ignore
            ),
            file=file
        )


