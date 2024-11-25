from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Callable

from monjour.core.transformation import Transformation, Transformer

Ctx = TypeVar('Ctx', contravariant=True)
Val = TypeVar('Val')

class ExecutionBlock(Generic[Ctx, Val]):
    """
    An execution block is a container for a sequence of transformations that are executed in
    sequence. The block is responsible for managing the state of the execution and the arguments
    that are passed between the transformations.

    Execution blocks are not usually created directly, but are created by an executor `new_block`
    method. This way the exector can decide which type of execution block to create.
    """
    args: tuple[Ctx, Val]
    last_result: Val

    transformers: list[Transformer[Ctx, Val]]
    # update_fn: Callable[[tuple[Ctx, Val], Val], tuple[Ctx, Val]] = lambda args, result: (args[0], result)

    def __init__(self, initial_args: tuple[Ctx, Val]):
        self.args = initial_args
        self.last_result = initial_args[1]
        self.transformers = []

    # def enqueue(self, transformer: Transformer[Ctx, Val]):
    #     self.transformers.append(transformer)

    def exec(self, transformer: Transformer[Ctx, Val]) -> Val:
        self.last_result = transformer(*self.args)
        self.args = self.update_fn(self.args, self.last_result)
        return self.last_result

    def update_fn(self, args: tuple[Ctx, Val], result: Val) -> tuple[Ctx, Val]:
        return (args[0], result)

    # def run(self) -> Val:
    #     for transformer in self.transformers:
    #         self.exec(transformer)
    #     return self.last_result

class Executor(Generic[Ctx, Val]):
    """
    An executor is responsible for managing the execution of a sequence of transformations.
    The executor is usually created very early in a pipeline and is responsible for creating
    and managing the execution blocks that will be used to execute the transformations.
    """
    def new_block(self, initial_args: tuple[Ctx, Val]) -> ExecutionBlock[Ctx, Val]:
        return ExecutionBlock(initial_args)

##################################################
# Recording Executor
##################################################
class RecordingExcecutionBlock(ExecutionBlock[Ctx, Val]):
    """
    An execution block that records the transformations that are executed. This is useful for
    debugging and for keeping track of the transformations that were executed.
    """
    transformations: list[Transformation[Ctx, Val]]

    def __init__(self, initial_args: tuple[Ctx, Val]):
        super().__init__(initial_args)
        self.transformations = []

    def exec(self, transformer: Transformer[Ctx, Val]) -> Val:
        args_copy = (self.args[0].copy(), self.args[1].copy(deep=True)) # type: ignore
        result = transformer(*self.args)
        transformation = Transformation(transformer.name, args_copy,
                                        result.copy(deep=True), **transformer.extra_args) # type: ignore
        self.transformations.append(transformation)
        if len(self.transformers) < len(self.transformations):
            self.transformers.append(transformer)
        self.args = self.update_fn(self.args, self.last_result)
        return result

class RecordingExecutor(Executor[Ctx, Val]):
    """
    An executor that produces recording execution blocks. This executor is useful for debugging
    """
    # Declarations
    blocks: list[RecordingExcecutionBlock[Ctx, Val]]

    def __init__(self):
        super().__init__()
        self.blocks = []

    def new_block(self, initial_args: tuple[Ctx, Val]) -> RecordingExcecutionBlock[Ctx, Val]:
        block = RecordingExcecutionBlock(initial_args)
        self.blocks.append(block)
        return block

    def get_all_transformations(self) -> list[Transformation[Ctx, Val]]:
        return [t for block in self.blocks for t in block.transformations]

    def get_all_declared_transformers(self) -> list[Transformer[Ctx, Val]]:
        return [t for block in self.blocks for t in block.transformers]
