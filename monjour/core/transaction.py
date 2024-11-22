from types import NoneType
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING, Optional, TypeAlias, get_args, Union
from enum import Enum

if TYPE_CHECKING:
    from monjour.core.archive import ArchiveID

class PaymentType(Enum):
    """
    Certain transactions require special treatment based on the payment type
    """
    Ecommerce           = 'Ecommerce'
    CardPayment         = 'CardPayment'
    Transfer            = 'Transfer'
    InternalTransfer    = 'InternalTransfer'
    Refund              = 'Refund'
    Withdrawal          = 'Withdrawal'
    Deposit             = 'Deposit'
    PreauthorizedDebit  = 'PreauthorizedDebit'

TransactionID: TypeAlias = str

@dataclass
class Transaction:
    ##############################################
    # Bookkeeping
    ##############################################

    # The unique identifier for the transaction
    # id: TransactionID

    # Unique identifier for the file that the transaction was imported from
    archive_id: str

    ##############################################
    # Required fields
    ##############################################

    # Date of the transaction
    date: pd.Timestamp

    # Amount of the transaction
    amount: np.float64

    # Currency of the transaction
    currency: str

    # Description of the transaction (Maybe make this required?)
    desc: str

    ##############################################
    # Optional fields filled by the importer
    ##############################################

    # Counterpart of the transaction
    counterpart: Optional[str]

    # Geographic location of the transaction|Website address|Phone number?
    location: Optional[str]

    # Special type of the transaction
    payment_type: Optional[PaymentType]

    # Details related to the payment method
    payment_type_details: Optional[str] # json

    # Anything extra that the importer wants to store
    extra: Optional[str] # json

    # Some transaction (for example refunds) need to reference another transaction
    ref: Optional[str]

    ##############################################
    # Optional fields filled by the user/automation
    ##############################################

    # Any user notes related to the transaction
    notes: Optional[str]

    # Category of the transaction
    category: Optional[str]

    # NOTE: This is not an exhaustive list of fields, more fields can be added as needed

    ##############################################
    # Aggregated Annotations
    ##############################################
    @classmethod
    def get_annotations(cls):
        # Traverse MRO to gather annotations from all parent classes
        annotations = {}
        for base in cls.__mro__:
            if hasattr(base, "__annotations__"):
                annotations.update(base.__annotations__)
        return annotations

    ##############################################
    # Conversion methods
    ##############################################
    @classmethod
    def to_pd_dtype_dict(cls):
        dtypes = {}
        for k, v in cls.get_annotations().items():
            ty = v
            if getattr(v, '__origin__', None) == Union:
                args = get_args(v)
                if len(args) != 2:
                    raise ValueError(f'Union type with more than 2 args is not supported: {v}')
                elif args[1] != NoneType:
                    raise ValueError(f'Union type with NoneType as second arg is not supported: {v}')
                ty = args[0]
            if ty == str:
                dtypes[k] = 'string'
            elif ty == np.float64:
                dtypes[k] = 'float64'
            elif ty == pd.Timestamp:
                dtypes[k] = 'datetime64[s]'
            elif isinstance(ty, type) and issubclass(ty, Enum):
                dtypes[k] = pd.CategoricalDtype(categories=[c.value for c in ty])
            else:
                dtypes[k] = 'object'
        return dtypes

    @classmethod
    def to_pa_model(cls):
        from pandera import Column, DataFrameSchema
        columns = {k: Column(v) for k, v in cls.to_pd_dtype_dict().items()}
        return DataFrameSchema(columns)

    @classmethod
    def from_pd_series(cls, series: pd.Series):
        return cls(**series.to_dict())

    @classmethod
    def to_empty_df(cls):
        initial_data = {k: pd.Series([], dtype=v) for k, v in cls.to_pd_dtype_dict().items()}
        return pd.DataFrame(initial_data)

    @classmethod
    def get_attribute_names(cls):
        return cls.get_annotations().keys()