from enum import Enum
from typing import Any
from functools import partialmethod
import logging

from monjour.core.log import MjLogger

class DiagnosticSeverity(Enum):
    Error = 1
    Warning = 2
    Info = 3
    Hint = 4
    Debug = 5

    def to_logging_int(self) -> int:
        match self:
            case DiagnosticSeverity.Error:
                return logging.ERROR
            case DiagnosticSeverity.Warning:
                return logging.WARNING
            case DiagnosticSeverity.Info:
                return logging.INFO
            case DiagnosticSeverity.Hint:
                return logging.INFO
            case DiagnosticSeverity.Debug:
                return logging.DEBUG

class Diagnostic:
    type: DiagnosticSeverity
    msg: str
    args: list[Any]
    kwargs: dict[str, Any]

    def __init__(self, type: DiagnosticSeverity, msg: str, *args, **kwargs):
        self.type = type
        self.msg = msg
        self.args = list(args)
        self.kwargs = kwargs

    def __str__(self):
        str = self.msg.format(*self.args, **self.kwargs)
        return str

    def __repr__(self):
        return f"<Diagnostic {self.type.name}: {self.msg}> {self.args} {self.kwargs}"

class DiagnosticCollector:
    logger: logging.Logger
    diagnostics: list[Diagnostic]

    def __init__(self, logger_name: str):
        self.diagnostics = []
        self.logger = MjLogger(logger_name)

    def _diag_prefix(self) -> str:
        """To be overridden by subclasses to provide a prefix for diagnostics."""
        return ''

    def _record_diag_internal(self, diag_type: DiagnosticSeverity, msg: str, *payload, **kwargs):
        diag = Diagnostic(diag_type, msg, *payload, **kwargs)
        self.logger.log(diag_type.to_logging_int(), self._diag_prefix() + str(diag))
        self.diagnostics.append(Diagnostic(diag_type, msg, *payload, **kwargs))

    diag_error   = partialmethod(_record_diag_internal, DiagnosticSeverity.Error)
    diag_warning = partialmethod(_record_diag_internal, DiagnosticSeverity.Warning)
    diag_info    = partialmethod(_record_diag_internal, DiagnosticSeverity.Info)
    diag_hint    = partialmethod(_record_diag_internal, DiagnosticSeverity.Hint)
    diag_debug   = partialmethod(_record_diag_internal, DiagnosticSeverity.Debug)

    def has_diag(self, diag_type: DiagnosticSeverity) -> bool:
        return any(diag.type == diag_type for diag in self.diagnostics)

    def get_diags(self, diag_type: DiagnosticSeverity) -> list[Diagnostic]:
        return [diag for diag in self.diagnostics if diag.type == diag_type]

    def st_show_diagnostics(self, filter: DiagnosticSeverity|None=None):
        import streamlit as st
        for diag in [d for d in self.diagnostics if filter is None or d.type == filter]:
            match diag.type:
                case DiagnosticSeverity.Error:
                    st.error(diag)
                case DiagnosticSeverity.Warning:
                    st.warning(diag)
                case DiagnosticSeverity.Info:
                    st.info(diag)
                case DiagnosticSeverity.Hint:
                    st.info(diag)
                case DiagnosticSeverity.Debug:
                    st.info(diag)

