import streamlit as st
import importlib

from streamlit.navigation.page import StreamlitPage
from pathlib import Path
from typing import Any

from monjour.app import App
from monjour.core.account import Account
from monjour.core.importer import ImporterInfo

@st.cache_resource
class StApp:
    home_dir: Path
    app: App
    config_module: Any

    def __init__(self, home_dir: Path|str):
        if isinstance(home_dir, str):
            home_dir = Path(home_dir)
        self.home_dir = home_dir

        self.config_module = importlib.import_module('configuration')
        self.app = self.config_module.app

    def find_custom_st_pages(self) -> list[StreamlitPage]:
        pages = []
        pages_dir = self.home_dir / 'pages'
        if not pages_dir.exists():
            return pages
        for page in list(pages_dir.glob('**/*.py')):
            pages.append(st.Page(page))
        return pages

    def list_all_importers(self) -> dict[str, list[ImporterInfo]]:
        importers = {}
        for acc in self.app.accounts.values():
            importers[acc.id] = acc.get_available_importers()
        return importers

    def list_importer_for_account(self, account_id: str) -> list[ImporterInfo]:
        acc = self.app.accounts[account_id]
        return acc.get_available_importers()

