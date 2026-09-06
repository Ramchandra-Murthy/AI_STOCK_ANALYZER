"""
EROS 3.0 public service facade.

The public API executes the EROS foundation stage followed by
the canonical valuation stage when sufficient input exists.

No valuation mathematics is performed here.
"""

from __future__ import annotations

from eros.decision.pipeline import (
    PipelineContext,
    create_context,
    finalize,
    run_foundation,
    run_valuation,
)


def evaluate(
    symbol: str,
    raw_data=None,
    **kwargs,
):
    """
    Execute the public EROS evaluation pipeline.

    Flow:

        raw input
            ↓
        foundation
            ↓
        valuation
            ↓
        finalize
    """

    context = create_context(symbol)

    # --------------------------------------------------------
    # FOUNDATION
    # --------------------------------------------------------

    run_foundation(
        context,
        raw_data=raw_data,
    )

    # --------------------------------------------------------
    # OPTIONAL CONTEXT OVERRIDES
    # --------------------------------------------------------

    for key, value in kwargs.items():
        if hasattr(context, key):
            setattr(context, key, value)

    # --------------------------------------------------------
    # VALUATION
    # --------------------------------------------------------

    # Only attempt valuation after foundation has produced
    # usable financial data.
    if context.financials is not None:
        run_valuation(context)

    # --------------------------------------------------------
    # FINAL PUBLIC RESULT
    # --------------------------------------------------------

    return finalize(context)


__all__ = [
    "evaluate",
]

