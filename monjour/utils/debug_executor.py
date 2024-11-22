from monjour.core.executor import *

class DebugExecutor(DeferredExecutor, Generic[Ctx, Val]):
    last_block: ExecutionBlock|None = None

    def __init__(self):
        super().__init__()

    def _run_impl(self, block: ExecutionBlock[Ctx, Val]) -> Val:
        args = block.initial_args
        self.on_run_requested(block)

        for transformer in block.transformation_decls:
            # Create a copy of the args and don't use it for the transformation
            args_copy = (args[0].copy(), args[1].copy(deep=True)) # type: ignore
            # Call the transformation
            result = transformer.fn(args[0], args[1])
            # Save the transformation
            transformation = Transformation(transformer.name,
                args_copy, result.copy(deep=True), **transformer.extra_args) # type:ignore
            block.transformations.append(transformation)
            # Update args for next call
            args = (args[0], result)
            self.on_transformation_applied(transformation)
        self.on_run_ended(args[1])
        return args[1]

    def on_run_requested(self, block: ExecutionBlock[Ctx, Val]):
        pass

    def on_transformation_applied(self, transformation: Transformation[Ctx, Val]):
        pass

    def on_run_ended(self, result: Val):
        pass
