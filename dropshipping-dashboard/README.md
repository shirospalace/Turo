# Dropshipping Dashboard

A local, single-user web dashboard for running a dropshipping side business
sourced from Sunsky-Online and sold on Amazon, eBay, and Etsy. Starting
niche is purses, but the data model is category-agnostic, so you can add
other categories later without a rebuild.

**Pure dropshipping**: nothing here assumes you hold, repack, or hand-touch
physical inventory — goods ship directly from Sunsky (or a fulfillment
partner) to the end customer. All 4 tabs are manual-review workflows;
nothing auto-publishes a listing or auto-places an order.

## Prerequisites checklist (do these outside the tool)

The app works today in manual-entry mode without any of this — features
that need an account/API key say so in the UI ("not connected") instead of
failing silently. Set these up as you're ready to go from research to
actually selling:

- [ ] **Amazon Seller Central** account
- [ ] **eBay** seller account **+** [eBay Developer Program](https://developer.ebay.com/) app registration (App ID / Cert ID) — needed for live Browse API comps
- [ ] **Etsy** shop **+** [Etsy Developer](https://www.etsy.com/developers/) app registration (API keystring) — needed for live Open API v3 comps
- [ ] **Sunsky-Online** account **+** Open API access request — needed to pull product data / create orders via API instead of CSV import or manual entry
- [ ] **Decide your return/refund policy** before selling for real: who eats return shipping, does Sunsky accept returns on unsold/defective units. Amazon, eBay, and Etsy each have minimum seller return-policy requirements — the Orders tab tracks return status/refunds but doesn't enforce or automate a policy.

## Setup

```bash
cd dropshipping-dashboard
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:8000 — a SQLite database (`dropshipping.db`) and
default seed data (a "Purses" category + Amazon/eBay/Etsy fee configs) are
created automatically on first run.

## How it's organized

- **Research tab** — add products by hand (cost, weight, warehouse, images)
  or import a Sunsky bulk CSV export; a margin calculator table shows
  editable target sale price, margin %, and margin $ per marketplace, with
  rows flagged red below your configurable margin threshold. Below that,
  log competitor comp prices per product — Amazon has no free official
  comp API so it's manual-only by design; eBay/Etsy comps are also manual
  until you wire up API keys (Phase 2). Comps are append-only, so price
  history builds up per product over time instead of overwriting.
- **Listings tab** — generate a draft listing per marketplace (Amazon
  title/bullets, eBay item specifics, Etsy tags/description) from an
  existing product. Everything is editable text you copy-paste yourself —
  nothing publishes automatically.
- **Orders tab** — log orders (marketplace order ID, sale price, Sunsky
  order ID) and move them through needs sourcing → ordered on Sunsky →
  shipped → delivered. Click an order to open its return/refund tracker
  (status, reason, refund amount, notes) — this is a simple status log, not
  an automated refund workflow.
- **Summary tab** — profit rollup (revenue, cost, refunds, net profit) by
  week or month, filterable by marketplace.
- **⚙ Fee Settings** (top right) — edit each marketplace's fee formula
  inputs (referral/FVF %, listing fee, payment processing) as fee schedules
  change, and see live API connection status for eBay/Etsy/Sunsky.

## Fee formulas

One generic formula (`services/margin.py`) covers all three marketplaces —
each one's quirks are just different fee-config values:

```
fees = listing_fee + sale_price * (variable_pct_1 + variable_pct_2) / 100
       + fixed_fee_1 + fixed_fee_2 + shipping_cost_estimate
net_profit = sale_price - fees - cost
margin_pct = net_profit / sale_price * 100
```

Seeded defaults: Amazon 15% referral; eBay 13.25% + $0.30 final value fee;
Etsy $0.20 listing fee + 6.5% transaction + 3% + $0.25 payment processing.

## Phase 2 — wiring up live APIs

CSV import (`services/sunsky_csv.py`) and manual entry work today with no
credentials. Once you have accounts from the checklist above, set these
environment variables and restart the app — the integration status badges
in Fee Settings will flip to "connected":

```
EBAY_APP_ID=...        EBAY_CERT_ID=...      # eBay Browse API (OAuth2 client-credentials)
ETSY_API_KEY=...                              # Etsy Open API v3 (keystring only for public search)
SUNSKY_API_KEY=...     SUNSKY_API_SECRET=...  # Sunsky Open API
```

`services/{ebay,etsy,sunsky}_api.py` have the auth flow documented in
comments and raise `NotImplementedError` for the actual API calls — the
client scaffolding is there, but wiring the live request/response mapping
is deliberately left for once you're actually testing against real
credentials (rate limits and response shapes are easiest to get right
against the live API, not guessed in advance).

## Future category expansion

`Category.halal_review_needed` exists in the data model but is unused for
purses. If you later add food, cosmetics, or supplements, flip that flag
and review sourcing for halal compliance before listing.
