# CareFi MEDUSDi Market Lab

**MEDUSDi is the asset. The AMM is the market. CareFi is the operator.**

This is an investor-facing Streamlit demo for the MEDUSDi roadshow. It combines a simple investor-allocation calculator with a Uniswap-style AMM simulator and LP revenue model, so investors can see both the exposure and the market mechanism.

## What it demonstrates

1. **Investor Allocation** — how many MEDUSDi an investor receives for a USDC allocation and the implied basis to medical-CPI fair value.
2. **AMM Market Simulator** — how a MEDUSDi/USDC pool reprices after buys/sells, including slippage and fees.
3. **LP Revenue Engine** — how CareFi can earn LP fees by operating liquidity around the market.
4. **Spot vs Fair Value Basis** — how AMM spot can be compared to medical-CPI fair value and a future prediction-market signal.
5. **Market Flywheel** — the roadshow close: CareFi seeds liquidity, creates price discovery, earns fees, and builds the reference layer.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

- Repository: `Oriel-CareFi/carefi-medusdi-market-lab`
- Main file path: `app.py`
- Python version: 3.11+

## Disclaimer

This demo uses synthetic inputs and simplified AMM math for investor education. It is not investment advice, not a token sale document, and not a representation of live Uniswap liquidity, pricing, fees, or returns.
