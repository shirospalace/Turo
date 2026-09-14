"""Marketplace fee/margin calculation.

One generic formula covers Amazon, eBay, and Etsy — each marketplace's quirks
are expressed by how MarketplaceFeeConfig's fields are populated (see seed.py):

    fees = listing_fee
           + sale_price * (variable_pct_1 + variable_pct_2) / 100
           + fixed_fee_1 + fixed_fee_2
           + shipping_cost_estimate
    net_profit = sale_price - fees - cost
    margin_pct = net_profit / sale_price * 100      (profit as % of revenue)
    markup_pct = net_profit / cost * 100             (profit as % of cost)

Seed defaults:
  Amazon: listing_fee=0,   var1=15   (referral), fixed1=0,    var2=0, fixed2=0
  eBay:   listing_fee=0,   var1=13.25 (FVF),      fixed1=0.30, var2=0, fixed2=0
  Etsy:   listing_fee=0.20, var1=6.5 (transaction), fixed1=0,  var2=3.0 (payment), fixed2=0.25
"""
from dataclasses import dataclass


@dataclass
class MarginResult:
    marketplace: str
    sale_price: float
    cost: float
    shipping_cost_estimate: float
    fees: float
    net_profit: float
    margin_pct: float
    markup_pct: float


def calculate_margin(cost, sale_price, shipping_cost_estimate, fee_config) -> MarginResult:
    sale_price = sale_price or 0.0
    cost = cost or 0.0
    shipping_cost_estimate = shipping_cost_estimate or 0.0

    variable_fees = sale_price * ((fee_config.variable_pct_1 + fee_config.variable_pct_2) / 100.0)
    fees = (
        fee_config.listing_fee
        + variable_fees
        + fee_config.fixed_fee_1
        + fee_config.fixed_fee_2
        + shipping_cost_estimate
    )
    net_profit = sale_price - fees - cost
    margin_pct = (net_profit / sale_price * 100.0) if sale_price > 0 else 0.0
    markup_pct = (net_profit / cost * 100.0) if cost > 0 else 0.0

    return MarginResult(
        marketplace=fee_config.marketplace,
        sale_price=round(sale_price, 2),
        cost=round(cost, 2),
        shipping_cost_estimate=round(shipping_cost_estimate, 2),
        fees=round(fees, 2),
        net_profit=round(net_profit, 2),
        margin_pct=round(margin_pct, 2),
        markup_pct=round(markup_pct, 2),
    )
