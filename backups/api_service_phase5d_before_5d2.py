"""
EROS 3.0 public service facade.
"""

from eros.decision.pipeline import (
    create_context,
    finalize,
    run_foundation,
)


def evaluate(
    symbol: str,
    raw_data=None,
    **kwargs,
):
    context = create_context(symbol)

    if raw_data is not None:
        run_foundation(
            context,
            raw_data=raw_data,
        )

    for key, value in kwargs.items():
        if hasattr(context, key):
            setattr(context, key, value)

    return finalize(context)


__all__ = ["evaluate"]
