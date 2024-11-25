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
    # Payment made with a card
    CardPayment         = 'CardPayment'

    # Transfer from/to another external bank account
    Transfer            = 'Transfer'

    # Transfer from/to another account defined in the app
    InternalTransfer    = 'InternalTransfer'

    # Refund of a previous transaction
    Refund              = 'Refund'

    # Withdrawal from the account
    Withdrawal          = 'Withdrawal'

    # Deposit to the account
    Deposit             = 'Deposit'

    # Recurring payment that is automatically debited from the account
    # e.g. utilities
    PreauthorizedDebit  = 'PreauthorizedDebit'

TransactionID: TypeAlias = str

@dataclass
class Transaction:
    """
    This class represent the standard transaction object used thoughtout the codebase.
    It rarely gets instantiated directly, but it is useful as a schema for untyped dataframes.

    - Importers have the goal of converting raw data into a list of transactions of this type.
    - The main dataframe in App is a collection of transactions of this type, with the attribute names
        being the column names of the dataframe and the type annotations being the types of the columns.
        The converison between the two is done by the to_pd_dtype_dict method.
    """
    ##############################################
    # Bookkeeping variables
    ##############################################

    # The unique identifier for the transaction
    # id: TransactionID

    # Unique identifier for the account that the transaction belongs to
    account_id: str

    # Unique identifier for the file that the transaction was imported from
    archive_id: str

    ##############################################
    # Required fields
    ##############################################

    # Date of the transaction (seconds precision)
    date: pd.Timestamp

    # Amount of the transaction
    amount: float

    # Currency of the transaction
    currency: str

    # Description of the transaction
    desc: str

    ##############################################
    # Optional fields filled by the importer
    ##############################################

    # Counterpart of the transaction
    counterpart: Optional[str]

    # Geographic location of the transaction|Website address|Phone number?
    location: Optional[str]

    # Special type of the transaction (PaymentType enum)
    payment_type: Optional[PaymentType]

    # Details related to the payment method
    # for example, card:1234 references the card with the last 4 digits 1234
    payment_type_details: Optional[str]

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
    # Categories can be nested for example Expenses/Utilities
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
        if getattr(cls, '_dtype_dict', None):
            return cls._dtype_dict
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
            if ty == float:
                dtypes[k] = 'float64'
            elif ty == pd.Timestamp:
                dtypes[k] = 'datetime64[s]'
            elif isinstance(ty, type) and issubclass(ty, Enum):
                dtypes[k] = pd.CategoricalDtype(categories=[c.value for c in ty])
            else:
                dtypes[k] = 'object'
        cls._dtype_dict = dtypes
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