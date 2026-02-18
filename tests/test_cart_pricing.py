import pytest

from backend.cart_pricing import (
    CartItem,
    calculate_cart_line_items,
    calculate_cart_total_cents,
)


BASIC_PRICE = 1200   # $12
ENRICHED_PRICE = 2400  # $24


def _unpack(line_items):
    """
    Helper to make assertions easier:
    returns list of tuples (pack_id, tier, price, qty, is_discounted)
    """
    return [
        (li.pack_id, li.enrichment_tier, li.unit_price_cents, li.quantity, li.is_discounted)
        for li in line_items
    ]


def test_empty_cart_returns_empty_line_items():
    assert calculate_cart_line_items([]) == []


def test_single_pack_no_discount():
    cart = [CartItem(pack_id="p1", enrichment_tier="basic", unit_price_cents=BASIC_PRICE, quantity=1)]
    line_items = calculate_cart_line_items(cart)
    items = _unpack(line_items)

    assert items == [("p1", "basic", BASIC_PRICE, 1, False)]
    assert calculate_cart_total_cents(line_items) == BASIC_PRICE


def test_two_packs_no_discount():
    cart = [
        CartItem("p1", "basic", BASIC_PRICE, quantity=1),
        CartItem("p2", "basic", BASIC_PRICE, quantity=1),
    ]
    line_items = calculate_cart_line_items(cart)
    items = _unpack(line_items)

    # Both full price, no discount
    assert items == [
        ("p1", "basic", BASIC_PRICE, 1, False),
        ("p2", "basic", BASIC_PRICE, 1, False),
    ]
    assert calculate_cart_total_cents(line_items) == BASIC_PRICE * 2


def test_third_pack_is_half_price():
    cart = [
        CartItem("p1", "basic", BASIC_PRICE, quantity=1),
        CartItem("p2", "basic", BASIC_PRICE, quantity=1),
        CartItem("p3", "basic", BASIC_PRICE, quantity=1),
    ]
    line_items = calculate_cart_line_items(cart)
    items = _unpack(line_items)

    # 1st & 2nd full price, 3rd half price
    assert items == [
        ("p1", "basic", BASIC_PRICE, 1, False),
        ("p2", "basic", BASIC_PRICE, 1, False),
        ("p3", "basic", BASIC_PRICE // 2, 1, True),
    ]
    total = calculate_cart_total_cents(line_items)
    assert total == BASIC_PRICE * 2 + BASIC_PRICE // 2


def test_six_packs_third_and_sixth_discounted():
    cart = [
        CartItem("p1", "basic", BASIC_PRICE, quantity=6),
    ]
    line_items = calculate_cart_line_items(cart)
    items = _unpack(line_items)

    # Order: full, full, half, full, full, half.
    # They all have same pack_id/tier/price grouping, so you should see:
    # [full x2, half x1, full x2, half x1]
    assert items == [
        ("p1", "basic", BASIC_PRICE, 2, False),
        ("p1", "basic", BASIC_PRICE // 2, 1, True),
        ("p1", "basic", BASIC_PRICE, 2, False),
        ("p1", "basic", BASIC_PRICE // 2, 1, True),
    ]
    total = calculate_cart_total_cents(line_items)
    expected = BASIC_PRICE * 4 + (BASIC_PRICE // 2) * 2  # 4 full + 2 half
    assert total == expected


def test_mixed_basic_and_enriched_respects_order_for_discounts():
    cart = [
        CartItem("p1", "basic", BASIC_PRICE, quantity=1),      # #1 full
        CartItem("p2", "enriched", ENRICHED_PRICE, quantity=1),# #2 full
        CartItem("p3", "basic", BASIC_PRICE, quantity=1),      # #3 half
        CartItem("p4", "enriched", ENRICHED_PRICE, quantity=1),# #4 full
        CartItem("p5", "basic", BASIC_PRICE, quantity=1),      # #5 full
        CartItem("p6", "enriched", ENRICHED_PRICE, quantity=1),# #6 half
    ]

    line_items = calculate_cart_line_items(cart)
    items = _unpack(line_items)

    # Check each position
    assert items[0] == ("p1", "basic", BASIC_PRICE, 1, False)
    assert items[1] == ("p2", "enriched", ENRICHED_PRICE, 1, False)
    assert items[2] == ("p3", "basic", BASIC_PRICE // 2, 1, True)   # #3 discounted
    assert items[3] == ("p4", "enriched", ENRICHED_PRICE, 1, False)
    assert items[4] == ("p5", "basic", BASIC_PRICE, 1, False)
    assert items[5] == ("p6", "enriched", ENRICHED_PRICE // 2, 1, True)  # #6 discounted

    total = calculate_cart_total_cents(line_items)
    expected = (
        BASIC_PRICE + ENRICHED_PRICE               # p1, p2
        + BASIC_PRICE // 2                         # p3 half
        + ENRICHED_PRICE + BASIC_PRICE             # p4, p5
        + ENRICHED_PRICE // 2                      # p6 half
    )
    assert total == expected


def test_quantities_are_expanded_before_discount():
    # 2 of p1, then 1 of p2: order of units is [p1, p1, p2]
    cart = [
        CartItem("p1", "basic", BASIC_PRICE, quantity=2),
        CartItem("p2", "basic", BASIC_PRICE, quantity=1),
    ]

    line_items = calculate_cart_line_items(cart)
    items = _unpack(line_items)

    # Units:
    #  #1 p1 full
    #  #2 p1 full
    #  #3 p2 half (discount)
    assert items == [
        ("p1", "basic", BASIC_PRICE, 2, False),
        ("p2", "basic", BASIC_PRICE // 2, 1, True),
    ]
