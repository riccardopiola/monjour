import streamlit as st

from typing import Any, Generic, TypeVar, Callable

T = TypeVar('T')

@st.cache_resource
class StateManager:
    pages: dict[str, set[str]]

    def __init__(self):
        print("Created StateManager")
        self.pages = dict()

    def register(self, page: str, key: str) -> str:
        self.pages.setdefault(page, set()).add(key)
        return f"{page}::{key}"

    def clear(self, page: str):
        if (key_list := self.pages.get(page)) is not None:
            for key in key_list:
                st.session_state.pop(key)
                key_list.remove(key)

    def clear_all(self):
        for page in self.pages:
            self.clear(page)

class use_state(Generic[T]):
    session_id: str

    def __init__(self, module: str, key: str, default: Callable[[], T]):
        self.session_id = StateManager().register(module, key)
        if self.session_id not in st.session_state:
            st.session_state[self.session_id] = default()

    def set(self, value: T):
        st.session_state[self.session_id] = value

    def get(self) -> T:
        return st.session_state[self.session_id]

    def __iter__(self):
        yield self.get()
        yield self.set


