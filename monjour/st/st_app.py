import streamlit as st
import importlib
import pandas as pd

from streamlit.navigation.page import StreamlitPage
from pathlib import Path
from typing import Any, Literal, TypeVar, Callable, Generic

from monjour.app import App
from monjour.core.account import Account
from monjour.core.importer import ImporterInfo

COUNTER = 0
def new_key(base: str):
    global COUNTER
    COUNTER += 1
    return f"{base}_{COUNTER}"

@st.cache_resource
def get_st_app(home_dir: Path|str):
    return StApp(home_dir)

def monjour_app_cache(st_app: "StApp", key: str):
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            if key not in st.session_state:
                value = func(*args, **kwargs)
                st.session_state[key] = value
                return func(*args, **kwargs)
            return st.session_state[key]
        def listener(_):
            if key in st.session_state:
                del st.session_state[key]
        st_app.app._add_df_listener(listener)
        return wrapper
    return decorator


T = TypeVar('T')

class StateAccessor(Generic[T]):
    id: str

    def __init__(self, id: str):
        self.id = id

    def get(self) -> T:
        return st.session_state[self.id]

    def set(self, value: T):
        st.session_state[self.id] = value

    def append(self, value: Any):
        st.session_state[self.id].append(value)

    def clear(self):
        st.session_state[self.id].clear()

class StApp:
    home_dir: Path
    app: App
    config_module: Any
    has_run: bool = False

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

    def copy(self, new_home_dir: Path|str):
        new_app = StApp(new_home_dir)
        new_app.app = self.app.copy()
        return new_app

    def run(self):
        self.app.run()
        self.has_run = True

    def state_default(self, module: str, key: str, default: Callable[..., T]) -> StateAccessor[T]:
        name = f"{module}_{key}"
        if name in st.session_state:
            return StateAccessor[T](name)
        st.session_state[name] = default()
        return StateAccessor[T](name)
