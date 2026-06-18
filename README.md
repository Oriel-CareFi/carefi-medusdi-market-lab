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
