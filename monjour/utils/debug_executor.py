from monjour.core.executor import *

class DebugExecutor(DeferredExecutor, Generic[Ctx, Val]):
    last_block: ExecutionBlock|None = None

    def __init__(self):
        super().__init__()

    def _run_impl(self, block: ExecutionBlock[Ctx, Val]) -> Val:
        args = block.initial_args
        self.on_run_requested(block)

        for transformer in block.transformation_decls:
            transformation = transformer.record_tranformation(*args)
            args = (args[0], transformation.result)
            block.transformations.append(transformation)
            self.on_transformation_applied(transformation)
        self.on_run_ended(args[1])
        return args[1]

    def on_run_requested(self, block: ExecutionBlock[Ctx, Val]):
        pass

    def on_transformation_applied(self, transformation: Transformation[Ctx, Val]):
        pass

    def on_run_ended(self, result: Val):
        pass
