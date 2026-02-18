from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, List


EnrichmentTier = Literal["basic", "enriched"]


@dataclass
class CartItem:
    """Raw cart item from frontend/backend before discount application."""
    pack_id: str
    enrichment_tier: EnrichmentTier
    unit_price_cents: int  # 1200 for $12, 2400 for $24
    quantity: int = 1


@dataclass
class PricedLineItem:
    """
    Aggregated line item after applying the
    'every 3rd pack is 50% off' rule.
    """
    pack_id: str
    enrichment_tier: EnrichmentTier
    unit_price_cents: int          # final unit price (full or 50% off)
    quantity: int                  # number of units at this price
    is_discounted: bool            # True if this block is the 50% units


def _expand_cart_to_units(cart: List[CartItem]) -> List[CartItem]:
    """
    Expand quantities into per-unit entries in order.
    Example:
        CartItem(quantity=3) -> 3 separate entries.
    """
    units: List[CartItem] = []
    for item in cart:
        for _ in range(item.quantity):
            units.append(
                CartItem(
                    pack_id=item.pack_id,
                    enrichment_tier=item.enrichment_tier,
                    unit_price_cents=item.unit_price_cents,
                    quantity=1,
                )
            )
    return units


def calculate_cart_line_items(cart: List[CartItem]) -> List[PricedLineItem]:
    """
    Apply '3rd pack 50% off' rule and return aggregated line items.

    Algorithm:
    1. Expand the cart into a flat list of units (respecting order).
    2. Every 3rd unit (index 2, 5, 8, ...) is 50% off.
    3. Collapse consecutive units with same (pack_id, tier, price, is_discounted)
       into a single PricedLineItem.
    """
    if not cart:
        return []

    units = _expand_cart_to_units(cart)
    priced_units: List[tuple[CartItem, bool]] = []

    for idx, unit in enumerate(units):
        # idx is 0-based; we want every 3rd (3rd, 6th, 9th...) → (idx + 1) % 3 == 0
        is_discounted = ((idx + 1) % 3 == 0)
        priced_units.append((unit, is_discounted))

    # Collapse into aggregated line items
    line_items: List[PricedLineItem] = []
    current: PricedLineItem | None = None

    for unit, is_discounted in priced_units:
        effective_price = unit.unit_price_cents // 2 if is_discounted else unit.unit_price_cents

        if (
            current is not None
            and current.pack_id == unit.pack_id
            and current.enrichment_tier == unit.enrichment_tier
            and current.unit_price_cents == effective_price
            and current.is_discounted == is_discounted
        ):
            current.quantity += 1
        else:
            if current is not None:
                line_items.append(current)
            current = PricedLineItem(
                pack_id=unit.pack_id,
                enrichment_tier=unit.enrichment_tier,
                unit_price_cents=effective_price,
                quantity=1,
                is_discounted=is_discounted,
            )

    if current is not None:
        line_items.append(current)

    return line_items


def calculate_cart_total_cents(line_items: List[PricedLineItem]) -> int:
    """Utility to compute the final cart total in cents."""
    return sum(li.unit_price_cents * li.quantity for li in line_items)
