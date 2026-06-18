# CareFi MEDUSDi Float-to-Market Lab

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


## Step 5 value-story update

The enterprise-value section now separates:
- **Modeled CareFi value components**: inventory FV accretion, retained inventory FV, and capitalized LP revenue.
- **Strategic infrastructure upside**: shown separately as a qualitative callout rather than as a bar in the base value chart.

This avoids mixing hard modeled economics with subjective strategic option value.
