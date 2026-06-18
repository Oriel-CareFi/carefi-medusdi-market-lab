import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="CareFi MEDUSDi Market Lab",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

CARE_GREEN = "#24D6A5"
CARE_BLUE = "#38A9FF"
CARE_AMBER = "#F7C948"
BG = "#07131D"
CARD = "#0E2233"

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.1rem; padding-bottom: 2rem;}
    .hero {
        padding: 1.35rem 1.6rem;
        border: 1px solid rgba(36,214,165,.28);
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(36,214,165,.12), rgba(56,169,255,.07));
        margin-bottom: 1.1rem;
    }
    .hero h1 {font-size: 2.35rem; margin-bottom: .25rem;}
    .hero p {font-size: 1.05rem; color: #C7D5DF; margin-bottom: 0;}
    .callout {
        padding: 1rem 1.15rem;
        border-left: 4px solid #24D6A5;
        border-radius: 12px;
        background: rgba(14,34,51,.75);
        color: #EAF4F7;
        margin: .65rem 0 1rem 0;
    }
    .mini {
        color: #9CB4C2;
        font-size: .9rem;
    }
    div[data-testid="stMetricValue"] {font-size: 1.65rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@dataclass
class PoolResult:
    pre_price: float
    post_price: float
    med_out: float
    usdc_out: float
    fee_paid: float
    slippage_pct: float
    new_usdc: float
    new_med: float
    basis_to_fv_pct: float


def fmt_money(x: float) -> str:
    if abs(x) >= 1_000_000_000:
        return f"${x/1_000_000_000:,.2f}B"
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:,.2f}M"
    if abs(x) >= 1_000:
        return f"${x/1_000:,.1f}K"
    return f"${x:,.2f}"


def fmt_units(x: float) -> str:
    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:,.2f}M"
    if abs(x) >= 1_000:
        return f"{x/1_000:,.1f}K"
    return f"{x:,.2f}"


def constant_product_swap(usdc_reserve: float, med_reserve: float, trade_size: float, fee_bps: float, direction: str, fv: float) -> PoolResult:
    pre_price = usdc_reserve / med_reserve
    fee_rate = fee_bps / 10_000
    fee_paid = trade_size * fee_rate
    amount_in_after_fee = trade_size * (1 - fee_rate)
    k = usdc_reserve * med_reserve

    if direction == "Buy MEDUSDi with USDC":
        new_usdc = usdc_reserve + amount_in_after_fee
        new_med = k / new_usdc
        med_out = med_reserve - new_med
        avg_price = trade_size / max(med_out, 1e-9)
        usdc_out = 0
    else:
        new_med = med_reserve + amount_in_after_fee
        new_usdc = k / new_med
        usdc_out = usdc_reserve - new_usdc
        med_out = 0
        avg_price = usdc_out / max(trade_size, 1e-9)

    post_price = new_usdc / new_med
    slippage_pct = ((avg_price / pre_price) - 1) * 100 if direction.startswith("Buy") else ((pre_price / max(avg_price, 1e-9)) - 1) * 100
    basis_to_fv_pct = ((post_price / fv) - 1) * 100
    return PoolResult(pre_price, post_price, med_out, usdc_out, fee_paid, slippage_pct, new_usdc, new_med, basis_to_fv_pct)


def pool_curve(usdc_reserve: float, med_reserve: float):
    k = usdc_reserve * med_reserve
    med = np.linspace(max(med_reserve * 0.35, 1), med_reserve * 1.8, 180)
    usdc = k / med
    return med, usdc


def revenue_table(monthly_volume: float, fee_bps: float, carefi_share: float) -> pd.DataFrame:
    rows = []
    for label, mult in [("Launch", .25), ("Base", 1.0), ("Momentum", 3.0), ("Category", 10.0)]:
        volume = monthly_volume * mult
        gross = volume * fee_bps / 10_000
        carefi = gross * carefi_share
        rows.append({
            "Scenario": label,
            "Monthly Volume": volume,
            "Gross LP Fees / Month": gross,
            "CareFi LP Share": carefi_share,
            "CareFi Revenue / Month": carefi,
            "Annualized CareFi Revenue": carefi * 12,
        })
    return pd.DataFrame(rows)


st.sidebar.title("Market Lab Controls")
st.sidebar.caption("Synthetic scenario model for MEDUSDi roadshow discussion.")

preset_df = pd.read_csv("data/demo_presets.csv")
preset_name = st.sidebar.selectbox("Scenario preset", preset_df["scenario"].tolist(), index=1)
preset = preset_df[preset_df["scenario"] == preset_name].iloc[0]

page = st.sidebar.radio(
    "Roadshow flow",
    [
        "1 · Investor Allocation",
        "2 · AMM Market Simulator",
        "3 · LP Revenue Engine",
        "4 · Spot vs Fair Value Basis",
        "5 · Market Flywheel",
    ],
)

st.markdown(
    """
    <div class="hero">
      <h1>CareFi MEDUSDi Market Lab</h1>
      <p><b>MEDUSDi is the asset. The AMM is the market. CareFi is the operator.</b><br>
      An investor-facing simulator for medical-inflation exposure, AMM price discovery, and LP economics.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar.expander("Global assumptions", expanded=True):
    medical_cpi_fv = st.number_input("Medical-CPI fair value per MEDUSDi", min_value=0.25, max_value=5.0, value=float(preset.medical_cpi_fv), step=0.01)
    fee_bps = st.slider("Pool fee tier / bps", 1, 100, int(preset.fee_bps), step=1)
    carefi_lp_share = st.slider("CareFi LP ownership", 0.0, 1.0, float(preset.carefi_lp_share), step=0.05)

if page.startswith("1"):
    st.subheader("1 · Investor Allocation")
    st.markdown('<div class="callout">Start with the simple investor question: <b>what does USDC buy, and what basis does that imply versus medical-CPI fair value?</b></div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        allocation = st.number_input("USDC allocation", min_value=10_000, max_value=50_000_000, value=1_000_000, step=50_000)
    with c2:
        issue_price = st.number_input("MEDUSDi issue / entry price", min_value=0.25, max_value=5.0, value=1.00, step=0.01)
    with c3:
        sidecar_pct = st.slider("CareFi sidecar / warrant coverage", 0.0, 1.0, 0.20, step=0.05)
    with c4:
        warrant_uplift = st.slider("Illustrative sidecar upside", 0.0, 3.0, 1.0, step=0.1)

    med_units = allocation / issue_price
    implied_fv = med_units * medical_cpi_fv
    basis = (issue_price / medical_cpi_fv - 1) * 100
    effective_exposure = implied_fv / allocation
    sidecar_value = allocation * sidecar_pct * warrant_uplift

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("MEDUSDi delivered", fmt_units(med_units))
    m2.metric("Implied FV exposure", fmt_money(implied_fv))
    m3.metric("Entry basis to FV", f"{basis:+.1f}%")
    m4.metric("Effective FV per $1", f"${effective_exposure:,.2f}")

    st.markdown("#### Allocation stack")
    fig = go.Figure()
    fig.add_bar(x=["USDC Allocation", "Medical-CPI FV Exposure", "Illustrative Sidecar Value"], y=[allocation, implied_fv, sidecar_value])
    fig.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20), yaxis_title="Value", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    st.info("Roadshow line: buying MEDUSDi is exposure; investing in CareFi is exposure to the market layer around that exposure.")

elif page.startswith("2"):
    st.subheader("2 · AMM Market Simulator")
    st.markdown('<div class="callout">This is the wow moment: investors can watch a MEDUSDi / USDC pool become the first observable market price for medical-inflation exposure.</div>', unsafe_allow_html=True)

    a, b, c, d = st.columns(4)
    with a:
        usdc_reserve = st.number_input("Initial USDC reserve", min_value=10_000, max_value=100_000_000, value=int(preset.usdc_reserve), step=50_000)
    with b:
        med_reserve = st.number_input("Initial MEDUSDi reserve", min_value=10_000, max_value=100_000_000, value=int(preset.medusdi_reserve), step=50_000)
    with c:
        direction = st.selectbox("Trade direction", ["Buy MEDUSDi with USDC", "Sell MEDUSDi for USDC"])
    with d:
        trade_size = st.number_input("Trade size", min_value=1_000, max_value=25_000_000, value=250_000, step=10_000)

    result = constant_product_swap(usdc_reserve, med_reserve, trade_size, fee_bps, direction, medical_cpi_fv)
    carefi_fee = result.fee_paid * carefi_lp_share

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Pre-trade spot", f"${result.pre_price:,.4f}")
    m2.metric("Post-trade spot", f"${result.post_price:,.4f}")
    m3.metric("Slippage", f"{result.slippage_pct:,.2f}%")
    m4.metric("LP fees", fmt_money(result.fee_paid))
    m5.metric("CareFi fee share", fmt_money(carefi_fee))

    left, right = st.columns([1.15, .85])
    with left:
        med, usdc = pool_curve(usdc_reserve, med_reserve)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=med, y=usdc, mode="lines", name="x*y=k pool curve"))
        fig.add_trace(go.Scatter(x=[med_reserve], y=[usdc_reserve], mode="markers+text", name="Before", text=["Before"], textposition="top center", marker=dict(size=12)))
        fig.add_trace(go.Scatter(x=[result.new_med], y=[result.new_usdc], mode="markers+text", name="After", text=["After"], textposition="bottom center", marker=dict(size=12)))
        fig.update_layout(height=460, xaxis_title="MEDUSDi reserve", yaxis_title="USDC reserve", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20,r=20,t=30,b=20))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("#### Trade tape")
        if direction.startswith("Buy"):
            st.write(f"Investor buys **{fmt_units(result.med_out)} MEDUSDi** with **{fmt_money(trade_size)} USDC**.")
        else:
            st.write(f"Investor sells **{fmt_units(trade_size)} MEDUSDi** and receives **{fmt_money(result.usdc_out)} USDC**.")
        st.write(f"Pool price moves from **${result.pre_price:,.4f}** to **${result.post_price:,.4f}**.")
        st.write(f"Spot/FV basis after trade: **{result.basis_to_fv_pct:+.2f}%**.")
        st.write(f"CareFi earns **{fmt_money(carefi_fee)}** from this trade at current LP share.")
        st.caption("Simplified constant-product AMM math; real Uniswap v3 behavior depends on active ranges and liquidity distribution.")

elif page.startswith("3"):
    st.subheader("3 · LP Revenue Engine")
    st.markdown('<div class="callout">This page turns the demo into a business model: volume × fee tier × CareFi LP share.</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        monthly_volume = st.number_input("Monthly MEDUSDi/USDC volume", min_value=100_000, max_value=1_000_000_000, value=int(preset.monthly_volume), step=100_000)
    with c2:
        active_liquidity_share = st.slider("Active liquidity inside FV band", 0.05, 1.0, 0.65, step=0.05)
    with c3:
        fee_density_boost = st.slider("Concentrated-liquidity fee-density boost", 1.0, 8.0, 2.0, step=0.25)

    gross_fees = monthly_volume * fee_bps / 10_000
    carefi_revenue = gross_fees * carefi_lp_share * active_liquidity_share * fee_density_boost
    annual = carefi_revenue * 12

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gross LP fees / month", fmt_money(gross_fees))
    m2.metric("CareFi monthly LP revenue", fmt_money(carefi_revenue))
    m3.metric("Annualized", fmt_money(annual))
    m4.metric("Fee take on volume", f"{carefi_revenue/monthly_volume*100:.3f}%")

    df = revenue_table(monthly_volume, fee_bps, carefi_lp_share * active_liquidity_share * fee_density_boost)
    st.dataframe(
        df.style.format({
            "Monthly Volume": "${:,.0f}",
            "Gross LP Fees / Month": "${:,.0f}",
            "CareFi LP Share": "{:.0%}",
            "CareFi Revenue / Month": "${:,.0f}",
            "Annualized CareFi Revenue": "${:,.0f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    fig = go.Figure()
    fig.add_bar(x=df["Scenario"], y=df["Annualized CareFi Revenue"])
    fig.update_layout(height=390, yaxis_title="Annualized CareFi LP revenue", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20,r=20,t=30,b=20))
    st.plotly_chart(fig, use_container_width=True)

elif page.startswith("4"):
    st.subheader("4 · Spot vs Fair Value Basis")
    st.markdown('<div class="callout">The market-structure story: AMM spot can be compared to medical-CPI FV and future listed/prediction-market signals.</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        amm_spot = st.number_input("MEDUSDi AMM spot", min_value=0.10, max_value=5.0, value=1.04, step=0.01)
    with c2:
        prediction_signal = st.number_input("Forecast / prediction-market signal", min_value=0.10, max_value=5.0, value=1.07, step=0.01)
    with c3:
        fair_value = st.number_input("Medical-CPI fair value", min_value=0.10, max_value=5.0, value=medical_cpi_fv, step=0.01)

    basis_df = pd.DataFrame({
        "Pair": ["AMM spot vs FV", "Forecast signal vs FV", "AMM spot vs forecast signal"],
        "Basis %": [
            (amm_spot / fair_value - 1) * 100,
            (prediction_signal / fair_value - 1) * 100,
            (amm_spot / prediction_signal - 1) * 100,
        ],
    })

    m1, m2, m3 = st.columns(3)
    m1.metric("AMM vs FV", f"{basis_df.iloc[0]['Basis %']:+.2f}%")
    m2.metric("Forecast vs FV", f"{basis_df.iloc[1]['Basis %']:+.2f}%")
    m3.metric("AMM vs Forecast", f"{basis_df.iloc[2]['Basis %']:+.2f}%")

    fig = go.Figure()
    fig.add_bar(x=["AMM Spot", "Medical-CPI FV", "Forecast Signal"], y=[amm_spot, fair_value, prediction_signal])
    fig.update_layout(height=420, yaxis_title="Price / index-equivalent value", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20,r=20,t=30,b=20))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Basis table")
    st.dataframe(basis_df.style.format({"Basis %": "{:+.2f}%"}), use_container_width=True, hide_index=True)
    st.success("Roadshow line: a market price, a fair value, and a listed signal create the basis market.")

else:
    st.subheader("5 · CareFi Market Flywheel")
    st.markdown('<div class="callout">The close: investors should leave understanding why CareFi is more than the token issuer.</div>', unsafe_allow_html=True)

    steps = [
        ("1", "CareFi seeds liquidity", "Initial MEDUSDi/USDC pool establishes tradable depth."),
        ("2", "MEDUSDi begins trading", "The market produces a visible spot price for medical-inflation exposure."),
        ("3", "Spot/FV basis appears", "Fair-value gaps create trading, arbitrage, and narrative energy."),
        ("4", "Volume generates LP fees", "CareFi earns economics from the market layer, not just asset exposure."),
        ("5", "Liquidity improves credibility", "Better depth makes the price more useful to investors and partners."),
        ("6", "Market infrastructure compounds", "Reference credibility supports listed contracts, structured products, and institutional adoption."),
    ]

    cols = st.columns(3)
    for i, (num, title, body) in enumerate(steps):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='padding:1rem; border:1px solid rgba(36,214,165,.22); border-radius:16px; background:rgba(14,34,51,.72); min-height:155px; margin-bottom:1rem;'>
              <div style='font-size:.85rem; color:#24D6A5; font-weight:700;'>STEP {num}</div>
              <div style='font-size:1.15rem; font-weight:700; margin:.25rem 0;'>{title}</div>
              <div style='color:#C7D5DF;'>{body}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Investor takeaway")
    st.markdown(
        """
        **Buying MEDUSDi directly is exposure. Investing in CareFi is exposure to the market operator.**

        CareFi can participate in the economics of liquidity provision, market formation, fair-value reference creation, and future product expansion around medical inflation.
        """
    )
    st.warning("Demo uses simplified scenario math. It should not be presented as guaranteed returns, guaranteed liquidity, or investment advice.")
