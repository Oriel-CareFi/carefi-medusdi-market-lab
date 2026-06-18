# CareFi MEDUSDi Market Model

**The pool anchors the market. The equity owns the infrastructure.**

This Streamlit app models the CareFi / MEDUSDi investor thesis:

1. CareFi acquires the initial independent USDiMED float at a discount to medical-CPI fair value.
2. CareFi uses that inventory to anchor a MEDUSDi / USDC reference pool.
3. The AMM creates observable spot pricing, basis signals, and LP fee revenue.
4. CareFi equity accrues from inventory value, LP economics, retained inventory, and market-infrastructure optionality.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit

- Branch: `main`
- Main file path: `app.py`

## Core tagline

> MEDUSDi is the exposure. The initial float is the wedge. The USDC pool is the market. CareFi equity owns the operating leverage.


## Latest investor-facing updates

- Sidebar renamed to **CareFi Value Scenario**.
- Primary framing changed to **Pool Economics + Platform Equity**.
- Added **Investment Structure Lens** to separate CareFi note/equity exposure from pool/SPV/sidecar exposure.
- Added **Investor FAQ** addressing whether CareFi investors own the pool, whether pool investors own CareFi equity, and whether combined structures are possible.
- Removed “Roadshow” language.


## Step 5 value-story correction

Step 5 now separates base modeled value from strategic infrastructure upside.

Base modeled value chart includes only:
- Inventory FV accretion
- LP revenue value
- Retained inventory FV

Strategic infrastructure upside is shown separately as a callout and is not included in the base modeled value chart.


## v7 update

Added Market Context, Demand-Side Use Cases, Liquidity Development Path, and compact Step 1 acquisition bridge. The Kalshi / ForecastEx comparison FAQ is intentionally not included.


## v9 FAQ #4 update

FAQ #4 now clarifies that combined CareFi equity/pool exposure must be intentionally structured and that any pass-through USDiMED exposure should preserve underlying transfer, liquidity, holding-period, and market-development limitations unless otherwise approved and documented.


## v10 copy refinement

Changed investor-facing label from "Lab" to **CareFi MEDUSDi Market Model** and shortened Step 4 to **Step 4 — Organic Supply** to avoid awkward line breaks in the two-column layout.
