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

    def record_tranformation(self, ctx: Ctx, df: Val) -> Transformation[Ctx, Val]:
        # TODO: Fix this my making Ctx, Val bound to SupportDeepCopy or something like that
        args_copy = (ctx.copy(), df.copy()) # type: ignore
        result = self.fn(ctx, df)
        return Transformation(self.name, args_copy, result, **self.extra_args)

def transformer(name: str|None = None):
    def decorator(fn: Callable[[Ctx, Val], Val]) -> Transformer[Ctx, Val]:
        return Transformer[Ctx, Val](fn, name)
    return decorator
