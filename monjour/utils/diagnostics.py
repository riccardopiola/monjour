from enum import Enum
from typing import Any
from functools import partialmethod

import monjour.core.log as log

class DiagnosticType(Enum):
    Error = 1
    Warning = 2
    Info = 3
    Hint = 4
    Debug = 5

class Diagnostic:
    type: DiagnosticType
    msg: str
    payload: list[Any]

    def __init__(self, type: DiagnosticType, msg: str, payload: list[Any] = []):
        self.type = type
        self.msg = msg
        self.payload = payload

    def __str__(self):
        str = self.msg
        for p in self.payload:
            str += f" {p}"
        return str

class DiagnosticCollector:
    diagnostics: list[Diagnostic]
    _prefix: str

    def __init__(self, prefix=''):
        self.diagnostics = []
        self._prefix = prefix

    def set_diag_prefix(self, prefix: str):
        self._prefix = prefix

    def _record_diag_internal(self, diag_type: DiagnosticType, msg: str, *payload: Any):
        msg = self._prefix + msg
        self.diagnostics.append(Diagnostic(diag_type, msg, list(payload)))

    diag_error   = partialmethod(_record_diag_internal, DiagnosticType.Error)
    diag_warning = partialmethod(_record_diag_internal, DiagnosticType.Warning)
    diag_info    = partialmethod(_record_diag_internal, DiagnosticType.Info)
    diag_hint    = partialmethod(_record_diag_internal, DiagnosticType.Hint)
    diag_debug   = partialmethod(_record_diag_internal, DiagnosticType.Debug)

    def has_diag(self, diag_type: DiagnosticType) -> bool:
        return any(diag.type == diag_type for diag in self.diagnostics)

    def get_diags(self, diag_type: DiagnosticType) -> list[Diagnostic]:
        return [diag for diag in self.diagnostics if diag.type == diag_type]

    def log_all_diagnostics(self):
        for diag in self.diagnostics:
            match diag.type:
                case DiagnosticType.Error:
                    log.error(diag)
                case DiagnosticType.Warning:
                    log.warning(diag)
                case DiagnosticType.Info:
                    log.info(diag)
                case DiagnosticType.Hint:
                    log.info(diag)
                case DiagnosticType.Debug:
                    log.debug(diag)

    def st_show_diagnostics(self, filter: DiagnosticType|None=None):
        import streamlit as st
        for diag in [d for d in self.diagnostics if filter is None or d.type == filter]:
            match diag.type:
                case DiagnosticType.Error:
                    st.error(diag)
                case DiagnosticType.Warning:
                    st.warning(diag)
                case DiagnosticType.Info:
                    st.info(diag)
                case DiagnosticType.Hint:
                    st.info(diag)
                case DiagnosticType.Debug:
                    st.info(diag)

