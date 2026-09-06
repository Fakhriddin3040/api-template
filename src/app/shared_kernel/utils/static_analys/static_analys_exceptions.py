class StaticAnalysException(Exception): ...


class TypeAssertionException(StaticAnalysException):
    def __init__(self, target: type, base: type) -> None:
        self.message = (
            f"{target.__name__} is not a implementation of {base.__name__} class."
        )

    def __str__(self) -> str:
        return self.message
