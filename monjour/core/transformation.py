from typing import Callable, Generic, TypeVar, Any
from dataclasses import dataclass, field

Ctx = TypeVar('Ctx', contravariant=True)
Val = TypeVar('Val')

class Transformation(Generic[Ctx, Val]):
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
    name: str
    fn: Callable[[Ctx, Val], Val]
    extra_args: dict[str, Any]

    def __init__(self, fn: Callable[[Ctx, Val], Val], name: str|None=None, **extra_args):
        self.fn = fn
        self.name = name or fn.__name__
        self.extra_args = dict(extra_args) if extra_args else {}

def transformer(name: str|None = None):
    def decorator(fn: Callable[[Ctx, Val], Val]) -> Transformer[Ctx, Val]:
        return Transformer[Ctx, Val](fn, name)
    return decorator
