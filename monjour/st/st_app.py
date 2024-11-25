import streamlit as st
import importlib
import pandas as pd

from streamlit.navigation.page import StreamlitPage
from pathlib import Path
from typing import Any, Callable

from monjour.app import App
from monjour.core.importer import ImporterInfo

@st.cache_resource
def get_st_app(home_dir: Path|str):
    return StApp(home_dir)

def monjour_app_cache(key: str):
    def decorator(func: Callable[["StApp"], Any]):
        added_listener = False
        def wrapper(st_app: "StApp"):
            def wrapper2(st_app: "StApp"):
                if (value := st.session_state.get(key)) is not None:
                    return value
                st.session_state[key] = value = func(st_app)
                return value
            if not added_listener:
                def listener(_):
                    if key in st.session_state:
                        del st.session_state[key]
                st_app.app._add_df_listener(listener)
            return wrapper2(st_app)
        return wrapper
    return decorator

class StApp:
    home_dir: Path
    app: App
    config_module: Any
    dirty: bool = True

    _df_listeners: list[Callable[["StApp"], Any]] = []

    def __init__(self, home_dir: Path|str):
        if isinstance(home_dir, str):
            home_dir = Path(home_dir)
        self.home_dir = home_dir

        self.config_module = importlib.import_module('configuration')
        self.app = self.config_module.app
        self.app._add_df_listener(lambda _: self._call_df_listeners())

    ########################################################
    # Config info
    ########################################################

    def find_custom_st_pages(self) -> list[StreamlitPage]:
        pages = []
        pages_dir = self.home_dir / 'pages'
        if not pages_dir.exists():
            return pages
        for page in list(pages_dir.glob('**/*.py')):
            pages.append(st.Page(pages_dir / page))
        return pages

    def list_all_importers(self) -> dict[str, list[ImporterInfo]]:
        importers = {}
        for acc in self.app.accounts.values():
            importers[acc.id] = acc.get_available_importers()
        return importers

    def list_importer_for_account(self, account_id: str) -> list[ImporterInfo]:
        acc = self.app.accounts[account_id]
        return acc.get_available_importers()

    ########################################################
    # Commands
    ########################################################

    def run(self, force: bool = False):
        if self.dirty or force:
            self.app.run()
            self._call_df_listeners()
            self.dirty = False

    ########################################################
    # Utils
    ########################################################

    def copy(self, new_home_dir: Path|str):
        new_app = StApp(new_home_dir)
        new_app.app = self.app.copy()
        return new_app

    def set_dirty(self):
        self.dirty = True

    def add_df_listener(self, func: Callable[["StApp"], Any]):
        self._df_listeners.append(func)

    def _call_df_listeners(self):
        for listener in self._df_listeners:
            listener(self)
