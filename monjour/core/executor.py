from abc import ABC
import pandas as pd
from typing import Any, Callable, Iterable, Self, Protocol, TypeAlias, Generic, TypeVar
import copy

from monjour.core.transformation import Transformation, Transformer

Ctx = TypeVar('Ctx', contravariant=True)
Val = TypeVar('Val')

class ExecutionBlock(Generic[Ctx, Val]):
    # Setup
    name: str
    initial_args: tuple[Ctx, Val]
    # Declarations
    transformation_decls: list[Transformer[Ctx, Val]]
    # Declarations + Results (once they have been run)
    transformations: list[Transformation[Ctx, Val]]

    def __init__(
        self,
        name: str,
        initial_args: tuple[Ctx, Val],
    ):
        self.name = name
        self.initial_args = initial_args
        self.transformation_decls = []
        self.transformations = []

    def enqueue(self, func: Transformer[Ctx, Val]):
        self.transformation_decls.append(func)

    def __iadd__(self, func: Transformer[Ctx, Val]) -> Self:
        """Just syntactic sugar for ExecutionBlock.enqueue"""
        self.enqueue(func)
        return self

class Executor(ABC, Generic[Ctx, Val]):

    def enter(
        self,
        name: str,
        initial_args: tuple[Ctx, Val],
    ) -> ExecutionBlock[Ctx, Val]:
        ...

    def run(self, block: ExecutionBlock|None = None) -> Val:
        ...

    def reset(self):
        ...

    def get_last_result(self) -> Val|None:
        ...

#################################################
# DeferredExecutor
#################################################

class DeferredExecutor(Executor[Ctx, Val]):
    last_block: ExecutionBlock[Ctx, Val]|None = None
    last_result: Val|None = None

    def __init__(self):
        self.last_block = None
        self.last_result = None

    def enter(
        self,
        name: str,
        initial_args: tuple[Ctx, Val],
    ) -> ExecutionBlock:
        self.last_block = ExecutionBlock(name, initial_args)
        self.last_result = None
        return self.last_block

    def run(self, block: ExecutionBlock[Ctx, Val]|None = None) -> Val:
        if block is None:
            if self.last_block is None:
                raise ValueError('No block to run')
            block = self.last_block
        self.last_block = block
        return self._run_impl(block)

    def _run_impl(self, block: ExecutionBlock[Ctx, Val]) -> Val:
        args = block.initial_args
        for transformer in block.transformation_decls:
            self.last_result = transformer.fn(*args)
            args = (args[0], self.last_result)
        return args[1]

    def reset(self):
        self.last_block = None

    def get_last_result(self) -> Val | None:
        return self.last_result

#################################################
# ImmediateExecutor
#################################################

class ImmediateExecutionBlock(ExecutionBlock, Generic[Ctx, Val]):
    args: tuple[Ctx, Val]

    def __init__(
        self,
        name: str,
        initial_args: tuple[Ctx, Val],
    ):
        super().__init__(name, initial_args)
        self.args = self.initial_args

    @property
    def last_result(self) -> Val:
        return self.args[1]

    def enqueue(self, transformer: Transformer[Ctx, Val]):
        self.run_immediate(transformer)

    def run_immediate(self, transformer: Transformer[Ctx, Val]) -> Val:
        result = transformer.fn(*self.args)
        self.args = (self.args[0], result)
        return result
class ImmediateExecutor(Executor, Generic[Ctx, Val]):
    last_block: ImmediateExecutionBlock|None = None

    def enter(
        self,
        name: str,
        initial_args: tuple[Ctx, Val],
    ) -> ImmediateExecutionBlock:
        self.last_block = ImmediateExecutionBlock[Ctx, Val](name, initial_args)
        return self.last_block

    def run(self, block: ImmediateExecutionBlock|None = None) -> Val:
        if block is not None:
            self.last_block = block
        elif not self.last_block:
            raise ValueError('Executor.run was called without a block previously defined')
        return self.last_block.last_result

    def reset(self):
        self.last_block = None

    def get_last_result(self) -> Any | None:
        if self.last_block is None:
            return None
        return self.last_block.last_result
