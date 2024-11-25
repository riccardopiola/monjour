from typing import Callable, Generic, TypeVar, Any
from dataclasses import dataclass, field

Ctx = TypeVar('Ctx', contravariant=True)
Val = TypeVar('Val')

class Transformation(Generic[Ctx, Val]):
    """
    A transformation is a record of a function that was executed with a given set of arguments
    and produced a given result. It is used by RecordingExecutor for debugging and for keeping track
    of the transformations that were executed.
    """
    name: str
    args: tuple[Ctx, Val]
    result: Val
    extra_args: dict[str, Any]

    def __init__(self, name: str, args: tuple[Ctx, Val], result: Val, **extra_args):
        self.name = name
        self.args = args
        self.result = result
        self.extra_args = dict(extra_args) if extra_args else dict()

    def __str__(self) -> str:
        return f"Transformation({self.name})"

class Transformer(Generic[Ctx, Val]):
    """
    A transformer is a wrapper around a function that takes a context and an input value
    (usually a pd.DataFrame) and returns a new value of the same type.
    """
    name: str
    fn: Callable[[Ctx, Val], Val]
    extra_args: dict[str, Any]

    def __init__(self, fn: Callable[[Ctx, Val], Val], name: str|None=None, **extra_args):
        self.fn = fn
        self.name = name or fn.__name__
        self.extra_args = dict(extra_args) if extra_args else {}

    def __call__(self, ctx: Ctx, val: Val) -> Val:
        return self.fn(ctx, val)

def transformer(name: str|None = None):
    """
    Decorator for creating a Transformer object from a function.
    """
    def decorator(fn: Callable[[Ctx, Val], Val]) -> Transformer[Ctx, Val]:
        return Transformer[Ctx, Val](fn, name)
    return decorator
