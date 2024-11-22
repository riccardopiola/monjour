import streamlit as st
import datetime as dt
from dataclasses import dataclass
from typing import IO

import monjour.core.log as log
from monjour.core.common import DateRange
from monjour.core.account import Account
from monjour.core.importer import ImporterInfo, Importer

from monjour.st import StApp

@st.fragment
def account_selector(st_app: StApp) -> str:
    # Create a dropdown menu
    accounts = st_app.app.accounts

    return st.selectbox('Account', [account.id for account in accounts.values()],
        format_func=lambda id: f"{accounts[id].id} [{accounts[id].PROVIDER_ID}]")

@st.fragment
def importer_selector(st_app: StApp, account_id: str) -> ImporterInfo:
    # Importer selection
    account = st_app.app.accounts[account_id]
    importers = st_app.list_all_importers()
    all_importers = sorted(importers[account_id], key=lambda imp: imp.id == account.importer.info.id, reverse=True)
    importer_info = st.selectbox('Importer', all_importers,
                        format_func=lambda imp: imp.id)
    return importer_info

@dataclass
class FileImportOptions:
    account: Account
    importer: Importer
    date_range: DateRange
    file: IO[bytes]

@st.fragment
def file_import_options(st_app: StApp):
    (c1, c2) = st.columns(2)
    with c1:
        account_id = account_selector(st_app)
    with c2:
        importer_info = importer_selector(st_app, account_id)

    account = st_app.app.accounts[account_id]
    importer = account.set_importer(importer_info.id)

    if file := st.file_uploader('File'):
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
        date_range = st.date_input('Date range',
            value=(inferred_start, inferred_end),
            max_value=dt.datetime.now(), # not sure if this is necessary
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



