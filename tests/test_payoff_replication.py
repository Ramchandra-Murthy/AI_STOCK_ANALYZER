from decimal import Decimal

import pytest

from strategy.payoff_replication import (
    OptionType,
    PayoffPoint,
    PositionSide,
    replicate_piecewise_linear_payoff,
)


D = Decimal


@pytest.fixture
def book_example():
    points = (
        PayoffPoint(D("0"), D("10")),
        PayoffPoint(D("70"), D("50")),
        PayoffPoint(D("90"), D("110")),
        PayoffPoint(D("100"), D("40")),
    )
    return replicate_piecewise_linear_payoff(points, terminal_slope=D("2"))


def independent_book_target(underlying: Decimal) -> Decimal:
    """Independent piecewise interpolation of the four source points."""
    if underlying <= D("70"):
        return D("10") + D("4") / D("7") * underlying
    if underlying <= D("90"):
        return D("50") + D("3") * (underlying - D("70"))
    if underlying <= D("100"):
        return D("110") - D("7") * (underlying - D("90"))
    return D("40") + D("2") * (underlying - D("100"))


@pytest.mark.parametrize(
    ("underlying", "expected"),
    [
        (D("0"), D("10")),
        (D("70"), D("50")),
        (D("90"), D("110")),
        (D("100"), D("40")),
        (D("35"), D("30")),
        (D("80"), D("80")),
        (D("95"), D("75")),
        (D("150"), D("140")),
    ],
)
def test_book_example_matches_independent_values(book_example, underlying, expected):
    assert book_example.expiration_payoff(underlying) == expected
    assert book_example.expiration_payoff(underlying) == independent_book_target(
        underlying
    )


def test_book_example_has_expected_call_slope_positions(book_example):
    call_positions = [
        (leg.strike, leg.side, leg.quantity)
        for leg in book_example.legs
        if leg.option_type is OptionType.CALL
        and leg.strike in {D("0"), D("70"), D("90"), D("100")}
    ]
    assert call_positions == [
        (D("0"), PositionSide.LONG, D("4") / D("7")),
        (D("70"), PositionSide.LONG, D("17") / D("7")),
        (D("90"), PositionSide.SHORT, D("10")),
        (D("100"), PositionSide.LONG, D("9")),
    ]


def test_constant_adjustment_is_four_option_package(book_example):
    adjustment_legs = [leg for leg in book_example.legs if leg.option_type is OptionType.PUT]
    assert len(adjustment_legs) == 2
    assert book_example.expiration_payoff(D("0")) == D("10")
    assert book_example.expiration_payoff(D("5")) - book_example.expiration_payoff(
        D("0")
    ) == D("20") / D("7")


def test_replication_matches_target_over_dense_grid(book_example):
    tolerance = D("1e-25")
    for step in range(0, 2001):
        underlying = D(step) / D("10")
        difference = abs(
            book_example.expiration_payoff(underlying)
            - independent_book_target(underlying)
        )
        assert difference <= tolerance


@pytest.mark.parametrize(
    "points",
    [
        (),
        (PayoffPoint(D("0"), D("0")),),
        (PayoffPoint(D("1"), D("0")), PayoffPoint(D("2"), D("1"))),
        (PayoffPoint(D("0"), D("0")), PayoffPoint(D("0"), D("1"))),
    ],
)
def test_invalid_point_sets_are_rejected(points):
    with pytest.raises(ValueError):
        replicate_piecewise_linear_payoff(points, terminal_slope=D("0"))


def test_negative_underlying_is_rejected(book_example):
    with pytest.raises(ValueError, match="non-negative"):
        book_example.expiration_payoff(D("-1"))
