
from __future__ import annotations
from pathlib import Path
from math import isfinite
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

APP_DIR = Path(__file__).parent
SCENARIO_PATH = APP_DIR / "data" / "scenarios.csv"
LOGO_PATH = APP_DIR / "assets" / "carefi_logo.jpg"

st.set_page_config(page_title="CareFi MEDUSDi Market Model", page_icon="➕", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container { padding-top: 1.3rem; padding-bottom: 3rem; }
.carefi-hero { padding: 1.25rem 1.4rem; border: 1px solid rgba(0,230,195,0.20); border-radius: 22px; background: linear-gradient(135deg, rgba(0,230,195,0.12), rgba(14,116,244,0.08)); margin-bottom: 1.1rem; }
.carefi-eyebrow { font-size: 0.82rem; letter-spacing: .12em; text-transform: uppercase; color: #00E6C3; font-weight: 700; margin-bottom: .35rem; }
.carefi-title { font-size: 2.35rem; line-height: 1.05; font-weight: 800; color: #F5FAFF; margin-bottom: .55rem; }
.carefi-subtitle { font-size: 1.05rem; line-height: 1.45; color: rgba(245,250,255,.82); max-width: 980px; }
.metric-card { border: 1px solid rgba(255,255,255,.10); background: rgba(255,255,255,.035); border-radius: 18px; padding: 1rem 1.05rem; min-height: 112px; }
.metric-label { font-size: .78rem; color: rgba(245,250,255,.64); text-transform: uppercase; letter-spacing: .06em; margin-bottom: .25rem; }
.metric-value { font-size: 1.55rem; font-weight: 750; color: #F5FAFF; margin-bottom: .2rem; }
.metric-note { font-size: .84rem; color: rgba(245,250,255,.66); }
.section-copy { color: rgba(245,250,255,.78); font-size: 1.01rem; line-height: 1.5; margin-top: -.25rem; margin-bottom: .8rem; }
.callout { border-left: 4px solid #00E6C3; background: rgba(0,230,195,.08); padding: 1rem 1.15rem; border-radius: 14px; color: rgba(245,250,255,.88); margin: .8rem 0 1rem 0; }
div[data-testid="stMetric"] { background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.10); padding: .85rem .9rem; border-radius: 16px; }
</style>
""", unsafe_allow_html=True)

def fmt_usd(x: float, decimals: int = 0) -> str:
    if not isfinite(float(x)): return "—"
    if abs(x) >= 1_000_000_000: return f"${x/1_000_000_000:,.2f}B"
    if abs(x) >= 1_000_000: return f"${x/1_000_000:,.2f}M"
    if abs(x) >= 1_000: return f"${x/1_000:,.1f}K"
    return f"${x:,.{decimals}f}"

def fmt_num(x: float, decimals: int = 0) -> str:
    if abs(x) >= 1_000_000_000: return f"{x/1_000_000_000:,.2f}B"
    if abs(x) >= 1_000_000: return f"{x/1_000_000:,.2f}M"
    if abs(x) >= 1_000: return f"{x/1_000:,.1f}K"
    return f"{x:,.{decimals}f}"

def fmt_pct(x: float, decimals: int = 1) -> str:
    return f"{100*x:,.{decimals}f}%"

def metric_card(label: str, value: str, note: str = "") -> None:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>""", unsafe_allow_html=True)

def scenario_metrics(row):
    initial_float_s = float(row["initial_float"])
    carefi_capture_pct_s = float(row["carefi_capture_pct"])
    acquisition_price_s = float(row["acquisition_price"])
    medical_cpi_fv_s = float(row["medical_cpi_fv"])
    pool_medusdi_s = float(row["pool_medusdi"])
    monthly_volume_s = float(row["monthly_volume"])
    fee_bps_s = float(row["fee_bps"])
    carefi_lp_share_s = float(row["carefi_lp_share"])
    organic_usdi_sliced_s = float(row["organic_usdi_sliced"])
    med_slice_pct_s = float(row["med_slice_pct"])
    revenue_multiple_s = float(row["revenue_multiple"])

    carefi_med_acquired_s = initial_float_s * carefi_capture_pct_s
    acquisition_cost_s = carefi_med_acquired_s * acquisition_price_s
    fv_mark_s = carefi_med_acquired_s * medical_cpi_fv_s
    inventory_accretion_s = fv_mark_s - acquisition_cost_s
    retained_med_s = max(carefi_med_acquired_s - pool_medusdi_s, 0)
    retained_inventory_fv_s = retained_med_s * medical_cpi_fv_s
    annual_lp_fees_s = monthly_volume_s * (fee_bps_s / 10000) * 12
    carefi_annual_lp_revenue_s = annual_lp_fees_s * carefi_lp_share_s
    lp_revenue_value_s = carefi_annual_lp_revenue_s * revenue_multiple_s
    organic_med_supply_s = organic_usdi_sliced_s * med_slice_pct_s
    total_supply_s = initial_float_s + organic_med_supply_s
    carefi_supply_share_s = carefi_med_acquired_s / total_supply_s if total_supply_s else 0
    modeled_value_s = max(inventory_accretion_s, 0) + retained_inventory_fv_s + lp_revenue_value_s

    return {
        "Scenario": row["scenario"],
        "Modeled CareFi value": modeled_value_s,
        "Annual LP revenue": carefi_annual_lp_revenue_s,
        "Retained inventory FV": retained_inventory_fv_s,
        "Total MEDUSDi supply": total_supply_s,
        "CareFi supply share": carefi_supply_share_s,
        "LP revenue value": lp_revenue_value_s,
        "Embedded accretion": max(inventory_accretion_s, 0),
    }

def compute_modeled_value_for_sensitivity(monthly_volume_v, carefi_lp_share_v, revenue_multiple_v, retained_med_v, acquisition_price_v):
    acquisition_cost_v = carefi_med_acquired * acquisition_price_v
    fv_mark_v = carefi_med_acquired * medical_cpi_fv
    inventory_accretion_v = fv_mark_v - acquisition_cost_v
    retained_inventory_fv_v = max(retained_med_v, 0) * medical_cpi_fv
    annual_lp_fees_v = monthly_volume_v * (fee_bps / 10000) * 12
    carefi_annual_lp_revenue_v = annual_lp_fees_v * carefi_lp_share_v
    lp_revenue_value_v = carefi_annual_lp_revenue_v * revenue_multiple_v
    return max(inventory_accretion_v, 0) + retained_inventory_fv_v + lp_revenue_value_v


def cp_buy(usdc_reserve, med_reserve, usdc_in, fee_bps):
    fee = fee_bps / 10000
    usdc_after_fee = usdc_in * (1 - fee)
    k = usdc_reserve * med_reserve
    new_usdc = usdc_reserve + usdc_after_fee
    new_med = k / new_usdc if new_usdc else med_reserve
    med_out = med_reserve - new_med
    price_before = usdc_reserve / med_reserve if med_reserve else 0
    price_after = new_usdc / new_med if new_med else 0
    avg_price = usdc_in / med_out if med_out > 0 else 0
    slippage = (avg_price / price_before - 1) if price_before else 0
    return med_out, usdc_in*fee, price_before, price_after, avg_price, slippage, new_usdc, new_med

def cp_sell(usdc_reserve, med_reserve, med_in, fee_bps):
    fee = fee_bps / 10000
    med_after_fee = med_in * (1 - fee)
    k = usdc_reserve * med_reserve
    new_med = med_reserve + med_after_fee
    new_usdc = k / new_med if new_med else usdc_reserve
    usdc_out = usdc_reserve - new_usdc
    price_before = usdc_reserve / med_reserve if med_reserve else 0
    price_after = new_usdc / new_med if new_med else 0
    avg_price = usdc_out / med_in if med_in > 0 else 0
    slippage = (avg_price / price_before - 1) if price_before else 0
    return usdc_out, med_in*fee, price_before, price_after, avg_price, slippage, new_usdc, new_med

@st.cache_data
def load_scenarios():
    return pd.read_csv(SCENARIO_PATH)

scenarios = load_scenarios()

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(Image.open(LOGO_PATH), use_container_width=True)
    st.markdown("## CareFi Value Scenario")
    st.caption("Model how discounted USDiMED float, anchor LP economics, and CareFi equity value interact.")
    scenario_name = st.selectbox("Scenario preset", scenarios["scenario"].tolist(), index=1)
    row = scenarios.loc[scenarios["scenario"] == scenario_name].iloc[0]
    with st.expander("What this scenario represents", expanded=True):
        st.write(row["description"])

    st.markdown("### Float acquisition")
    initial_float = st.number_input("Initial independent USDiMED float", 100_000, 25_000_000, int(row.initial_float), step=100_000)
    carefi_capture_pct = st.slider("CareFi captured share of initial float", 0.0, 1.0, float(row.carefi_capture_pct), 0.05)
    acquisition_price = st.number_input("CareFi acquisition price per USDiMED", 0.50, 2.00, float(row.acquisition_price), step=0.01)
    medical_cpi_fv = st.number_input("Medical-CPI fair value per USDiMED", 0.50, 2.50, float(row.medical_cpi_fv), step=0.01)

    st.markdown("### Anchor LP pool")
    pool_medusdi = st.number_input("USDiMED allocated to pool", 0, 20_000_000, int(row.pool_medusdi), step=50_000)
    pool_usdc = st.number_input("USDC paired into pool", 0, 50_000_000, int(row.pool_usdc), step=50_000)
    fee_bps = st.slider("Pool fee tier / bps", 1, 100, int(row.fee_bps), 1)
    carefi_lp_share = st.slider("CareFi LP share", 0.0, 1.0, float(row.carefi_lp_share), 0.05)

    st.markdown("### Market activity")
    monthly_volume = st.number_input("Monthly MEDUSDi / USDC trading volume", 0, 1_000_000_000, int(row.monthly_volume), step=500_000)
    trade_size = st.number_input("Illustrative trade size", 0, 10_000_000, max(50_000, int(monthly_volume * 0.05)) if monthly_volume else 100_000, step=25_000)
    trade_direction = st.radio("Illustrative AMM trade", ["Buy MEDUSDi with USDC", "Sell MEDUSDi for USDC"])

    st.markdown("### Future supply & equity")
    organic_usdi_sliced = st.number_input("Future organic USDi sliced by third parties", 0, 1_000_000_000, int(row.organic_usdi_sliced), step=500_000)
    med_slice_pct = st.slider("Approx. MEDUSDi slice of USDi", 0.00, 0.25, float(row.med_slice_pct), 0.01)
    reference_option_value = st.number_input("Illustrative reference-market option value", 0, 100_000_000, int(row.reference_option_value), step=250_000)
    revenue_multiple = st.slider("LP revenue value multiple", 0, 25, int(row.revenue_multiple), 1)
    pre_money = st.number_input("CareFi pre-money valuation", 500_000, 100_000_000, int(row.pre_money), step=500_000)
    investor_check = st.number_input("Investor check size", 25_000, 25_000_000, int(row.investor_check), step=25_000)

carefi_med_acquired = initial_float * carefi_capture_pct
acquisition_cost = carefi_med_acquired * acquisition_price
fv_mark = carefi_med_acquired * medical_cpi_fv
inventory_accretion = fv_mark - acquisition_cost
discount_to_fv = (medical_cpi_fv - acquisition_price) / medical_cpi_fv if medical_cpi_fv else 0
pool_price = pool_usdc / pool_medusdi if pool_medusdi > 0 else 0
retained_med = max(carefi_med_acquired - pool_medusdi, 0)
retained_inventory_fv = retained_med * medical_cpi_fv
annual_lp_fees = monthly_volume * (fee_bps / 10000) * 12
carefi_annual_lp_revenue = annual_lp_fees * carefi_lp_share
lp_revenue_value = carefi_annual_lp_revenue * revenue_multiple
organic_med_supply = organic_usdi_sliced * med_slice_pct
total_med_supply_after = carefi_med_acquired + organic_med_supply
carefi_total_supply_share_after = carefi_med_acquired / total_med_supply_after if total_med_supply_after else 0

if pool_medusdi > 0 and pool_usdc > 0 and trade_size > 0:
    if trade_direction == "Buy MEDUSDi with USDC":
        trade_out, trade_fee_value_usd, price_before, price_after, avg_price, slippage, new_usdc, new_med = cp_buy(pool_usdc, pool_medusdi, trade_size, fee_bps)
    else:
        trade_out, fees_med, price_before, price_after, avg_price, slippage, new_usdc, new_med = cp_sell(pool_usdc, pool_medusdi, trade_size, fee_bps)
        trade_fee_value_usd = fees_med * medical_cpi_fv
else:
    trade_out = trade_fee_value_usd = 0
    price_before = price_after = avg_price = pool_price
    slippage = 0
    new_usdc, new_med = pool_usdc, pool_medusdi

spot_fv_basis = (price_after / medical_cpi_fv - 1) if medical_cpi_fv else 0
carefi_trade_fee_share = trade_fee_value_usd * carefi_lp_share
modeled_carefi_value = max(inventory_accretion, 0) + retained_inventory_fv + lp_revenue_value
illustrative_carefi_ev_accretion = modeled_carefi_value
post_money = pre_money + investor_check
investor_ownership = investor_check / post_money if post_money else 0
investor_value_from_accretion = illustrative_carefi_ev_accretion * investor_ownership
check_coverage = investor_value_from_accretion / investor_check if investor_check else 0

st.markdown("""
<div class="carefi-hero">
<div class="carefi-eyebrow">CareFi MEDUSDi Market Model</div>
<div class="carefi-title">The pool anchors the market. The equity owns the infrastructure.</div>
<div class="carefi-subtitle">Model how CareFi can acquire discounted USDiMED float, seed the MEDUSDi / USDC reference pool, earn anchor LP economics, and build enterprise value around healthcare inflation and cost-risk infrastructure.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""<div class="callout"><b>Pool Economics + Platform Equity:</b> the MEDUSDi / USDC pool is the anchor proof point. CareFi equity is the infrastructure upside around healthcare inflation and medical cost-risk surfaces.</div>""", unsafe_allow_html=True)

st.header("Market Context")
st.markdown("""<div class="section-copy">USDiMED is not just a pool asset. It is a tradeable spot proxy for a specific medical-care inflation exposure that has historically behaved differently from headline CPI.</div>""", unsafe_allow_html=True)

context_cols = st.columns(3)
with context_cols[0]:
    metric_card("Medical-CPI slice", "~8.3%", "Approximate USDiMED slice per $1.00 USDi split")
with context_cols[1]:
    metric_card("Latest index level", "593.239", "BLS CPIMEDNS, May 2026; 1982–84 = 100")
with context_cols[2]:
    metric_card("Structural basis", "~70% higher", "Medical care index rise versus all-items CPI since 1990")


st.header("Market Formation Timeline")
st.markdown("""<div class="section-copy">The strategy is a sequence: scarce float becomes an external spot market, the spot market creates basis and fee economics, and the reference point creates platform value.</div>""", unsafe_allow_html=True)

timeline_cols = st.columns(5)
with timeline_cols[0]:
    metric_card("1. Float capture", "Scarce inventory", "CareFi anchors the initial independent USDiMED position")
with timeline_cols[1]:
    metric_card("2. Spot pool", "USDC price", "MEDUSDi / USDC establishes an observable market")
with timeline_cols[2]:
    metric_card("3. Basis flow", "Price discovery", "Specialists compare spot, fair value, and medical CPI expectations")
with timeline_cols[3]:
    metric_card("4. Organic supply", "Slicing expands float", "USDi holders can create new MEDUSDi supply as the architecture develops")
with timeline_cols[4]:
    metric_card("5. Platform value", "Infrastructure layer", "CareFi uses the proof point to build reference, curve, and hedge products")

st.markdown("""
<div class="callout">
    <b>Flywheel:</b> early float control → MEDUSDi / USDC spot price → observable basis → specialist flow → organic slicing → deeper liquidity → stronger CareFi infrastructure story.
</div>
""", unsafe_allow_html=True)


st.header("Scenario Compare")
st.markdown("""<div class="section-copy">Compare the full market-formation path across presets. The progression shows how value shifts from initial inventory advantage toward LP revenue, retained inventory, and broader supply formation.</div>""", unsafe_allow_html=True)

compare_df = pd.DataFrame([scenario_metrics(r) for _, r in scenarios.iterrows()])
compare_display = compare_df.copy()
for col in ["Modeled CareFi value", "Annual LP revenue", "Retained inventory FV", "Total MEDUSDi supply", "LP revenue value", "Embedded accretion"]:
    compare_display[col] = compare_display[col].map(fmt_usd)
compare_display["CareFi supply share"] = compare_display["CareFi supply share"].map(fmt_pct)
st.dataframe(
    compare_display[["Scenario", "Modeled CareFi value", "Annual LP revenue", "Retained inventory FV", "Total MEDUSDi supply", "CareFi supply share"]],
    use_container_width=True,
    hide_index=True,
)

compare_fig = go.Figure()
compare_fig.add_bar(x=compare_df["Scenario"], y=compare_df["Modeled CareFi value"], name="Modeled CareFi value")
compare_fig.add_scatter(x=compare_df["Scenario"], y=compare_df["Annual LP revenue"], mode="lines+markers", name="Annual LP revenue", yaxis="y2")
compare_fig.update_layout(
    title="Scenario progression: value and fee formation",
    yaxis=dict(title="Modeled CareFi value", tickformat="$,.0f"),
    yaxis2=dict(title="Annual LP revenue", overlaying="y", side="right", tickformat="$,.0f"),
    height=430,
    margin=dict(l=20, r=20, t=55, b=95),
    legend=dict(orientation="h", y=-0.25),
)
st.plotly_chart(compare_fig, use_container_width=True)

st.header("Pool Economics + Platform Equity")
st.markdown("""<div class="section-copy">A direct MEDUSDi buyer owns the exposure. A CareFi investor owns the operating company positioned to acquire the initial float, anchor the first USDC-facing market, retain strategic inventory, earn LP economics, and commercialize the broader healthcare cost-risk infrastructure layer.</div>""", unsafe_allow_html=True)
c = st.columns(4)
with c[0]: metric_card("Embedded float accretion", fmt_usd(inventory_accretion), f"{fmt_pct(discount_to_fv)} discount to FV")
with c[1]: metric_card("CareFi annual LP revenue", fmt_usd(carefi_annual_lp_revenue), f"{fmt_pct(carefi_lp_share)} LP share at {fee_bps} bps")
with c[2]: metric_card("Retained inventory FV", fmt_usd(retained_inventory_fv), f"{fmt_num(retained_med)} MEDUSDi retained")
with c[3]: metric_card("Modeled CareFi value", fmt_usd(modeled_carefi_value), "Inventory + retained inventory + LP value")


st.subheader("Investment Structure Lens")
st.markdown("""<div class="section-copy">The model shows both value engines, but the investor's actual entitlement depends on the offering structure. CareFi note/equity investors, pool/SPV investors, and combined-structure investors may have different rights.</div>""", unsafe_allow_html=True)

lens_cols = st.columns(2)
with lens_cols[0]:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">CareFi note / equity investment</div>
        <div class="metric-value">Platform equity</div>
        <div class="metric-note">Exposure to CareFi as the operating company building healthcare inflation and cost-risk market infrastructure. Pool economics accrue only to the extent they are retained by, contracted to, or otherwise benefit CareFi.</div>
    </div>
    """, unsafe_allow_html=True)
with lens_cols[1]:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">Pool / SPV / sidecar investment</div>
        <div class="metric-value">Pool economics</div>
        <div class="metric-note">Direct or linked exposure to the MEDUSDi / USDC liquidity strategy if offered through a separate vehicle. CareFi equity is separate unless expressly included by the offering documents.</div>
    </div>
    """, unsafe_allow_html=True)


st.divider()
st.header("Demand-Side Use Cases")
st.markdown("""<div class="section-copy">The pool is the first observable market node. The broader opportunity is a reference layer for organizations that carry direct healthcare inflation or medical cost exposure.</div>""", unsafe_allow_html=True)

use_cols = st.columns(3)
with use_cols[0]:
    metric_card("Hospitals & health systems", "Budget hedge", "Multi-year cost-of-care inflation exposure")
with use_cols[1]:
    metric_card("Self-insured employers", "Benefit-cost hedge", "Employee health-benefit inflation exposure")
with use_cols[2]:
    metric_card("Insurers & managed care", "Premium basis", "Medical inflation versus embedded rate assumptions")

use_cols2 = st.columns(3)
with use_cols2[0]:
    metric_card("Pensions & retiree benefits", "Retiree medical", "Long-horizon healthcare inflation exposure")
with use_cols2[1]:
    metric_card("Structured products & swaps", "Reference rate", "Medical-CPI-linked notes, swaps, and bonds")
with use_cols2[2]:
    metric_card("Forward curve builders", "3-, 6-, 12-month curve", "Early holders help seed forward market infrastructure")

st.header("Step 1 — Initial Float Acquired Below Medical-CPI Fair Value")
st.markdown("""<div class="section-copy">CareFi’s launch wedge begins with control of the initial USDiMED float at a discount to its medical-CPI fair-value mark.</div>""", unsafe_allow_html=True)

st.subheader("Acquisition bridge")
bridge_cols = st.columns(3)
with bridge_cols[0]:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Acquisition cost</div>
        <div class="metric-value">{fmt_usd(acquisition_cost)}</div>
        <div class="metric-note">{fmt_num(carefi_med_acquired)} USDiMED acquired at {fmt_usd(acquisition_price)} per unit.</div>
    </div>
    """, unsafe_allow_html=True)
with bridge_cols[1]:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">+ Fair-value accretion</div>
        <div class="metric-value">{fmt_usd(max(inventory_accretion, 0))}</div>
        <div class="metric-note">Embedded accretion before secondary liquidity fully develops.</div>
    </div>
    """, unsafe_allow_html=True)
with bridge_cols[2]:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">= Medical-CPI FV mark</div>
        <div class="metric-value">{fmt_usd(fv_mark)}</div>
        <div class="metric-note">Fair-value mark at {fmt_usd(medical_cpi_fv)} per USDiMED.</div>
    </div>
    """, unsafe_allow_html=True)

st.subheader("The launch wedge: discounted float versus fair value")
spread_cols = st.columns(3)
with spread_cols[0]:
    metric_card("USDiMED acquisition price", fmt_usd(acquisition_price), "Price paid per USDiMED")
with spread_cols[1]:
    metric_card("Medical-CPI fair value", fmt_usd(medical_cpi_fv), "Fair-value mark per USDiMED")
with spread_cols[2]:
    metric_card("Embedded basis", f"{fmt_usd(medical_cpi_fv - acquisition_price)} / {fmt_pct(discount_to_fv)}", "Fair-value spread captured at launch")

st.markdown(f"""
<div class="callout">
    <b>Launch wedge:</b> {fmt_usd(acquisition_cost)} acquisition cost + {fmt_usd(max(inventory_accretion, 0))} fair-value accretion = {fmt_usd(fv_mark)} medical-CPI fair-value mark.
</div>
""", unsafe_allow_html=True)

st.header("Step 2 — CareFi Seeds the MEDUSDi / USDC Reference Pool")
st.markdown("""<div class="section-copy">CareFi uses part of its USDiMED inventory plus USDC to create the first external, observable spot price for healthcare inflation exposure. The AMM converts trading flow into price discovery, basis signals, and LP fee revenue.</div>""", unsafe_allow_html=True)
pool_cols = st.columns(5)
pool_cols[0].metric("USDiMED in pool", fmt_num(pool_medusdi))
pool_cols[1].metric("USDC in pool", fmt_usd(pool_usdc))
pool_cols[2].metric("Initial pool price", fmt_usd(pool_price, 2) if pool_price else "—")
pool_cols[3].metric("CareFi LP share", fmt_pct(carefi_lp_share))
pool_cols[4].metric("Retained MEDUSDi", fmt_num(retained_med))

st.subheader("AMM trading mechanics")
trade_cols = st.columns(6)
trade_cols[0].metric("Pre-trade price", fmt_usd(price_before, 4) if price_before else "—")
trade_cols[1].metric("Post-trade price", fmt_usd(price_after, 4) if price_after else "—")
trade_cols[2].metric("Avg execution price", fmt_usd(avg_price, 4) if avg_price else "—")
trade_cols[3].metric("Slippage", fmt_pct(slippage))
trade_cols[4].metric("Spot/FV basis", fmt_pct(spot_fv_basis))
trade_cols[5].metric("CareFi fee share", fmt_usd(carefi_trade_fee_share))

amm_fig = go.Figure()
amm_fig.add_bar(name="Before USDC", x=["USDC"], y=[pool_usdc])
amm_fig.add_bar(name="After USDC", x=["USDC"], y=[new_usdc])
amm_fig.add_bar(name="Before MEDUSDi", x=["MEDUSDi"], y=[pool_medusdi])
amm_fig.add_bar(name="After MEDUSDi", x=["MEDUSDi"], y=[new_med])
amm_fig.update_layout(barmode="group", title=f"Reserve shift after illustrative trade: {trade_direction}", yaxis_title="Units", height=390, margin=dict(l=20, r=20, t=55, b=30), legend=dict(orientation="h", y=-0.2))
st.plotly_chart(amm_fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.header("Step 3 — LP Revenue Formation")
    st.markdown("""<div class="section-copy">Trading volume generates fees. CareFi's economics are a function of fee tier, total pool volume, and CareFi's share of active liquidity.</div>""", unsafe_allow_html=True)
    st.metric("Monthly trading volume", fmt_usd(monthly_volume))
    st.metric("Gross annual LP fees", fmt_usd(annual_lp_fees))
    st.metric("CareFi annual LP revenue", fmt_usd(carefi_annual_lp_revenue))
    st.metric("LP revenue value", fmt_usd(lp_revenue_value), f"{revenue_multiple}x multiple")

with right:
    st.header("Step 4 — Organic Supply")
    st.markdown("""<div class="section-copy">CareFi's initial float advantage is strongest at launch. Over time, new MEDUSDi supply can emerge when third parties buy USDi and create medical slices.</div>""", unsafe_allow_html=True)
    st.metric("Organic USDi sliced", fmt_usd(organic_usdi_sliced))
    st.metric("New MEDUSDi supply", fmt_num(organic_med_supply), f"{fmt_pct(med_slice_pct)} medical slice")
    st.metric("Total modeled MEDUSDi supply", fmt_num(total_med_supply_after))
    st.metric("CareFi share after organic supply", fmt_pct(carefi_total_supply_share_after))

st.header("Liquidity Development Path")
st.markdown("""<div class="section-copy">The market does not need to arrive fully formed. The sequence is float control, external price formation, specialist flow, and then organic supply expansion through future slicing.</div>""", unsafe_allow_html=True)

path_cols = st.columns(4)
with path_cols[0]:
    metric_card("1. Initial allocation", "Scarce float", "CareFi / anchor holders acquire early USDiMED inventory")
with path_cols[1]:
    metric_card("2. Reference pool", "External spot", "MEDUSDi / USDC establishes a visible market price")
with path_cols[2]:
    metric_card("3. Specialist flow", "Basis trading", "Traders compare spot price, fair value, and expected medical CPI")
with path_cols[3]:
    metric_card("4. Organic slicing", "Supply growth", "USDi holders create new MEDUSDi supply as split/recombine develops")

st.markdown(f"""
<div class="callout">
    <b>Organic slicing math:</b> at an assumed {fmt_pct(med_slice_pct)} medical slice, every {fmt_usd(100)} of USDi split can create approximately {fmt_usd(100 * med_slice_pct)} of MEDUSDi supply.
</div>
""", unsafe_allow_html=True)

st.header("Step 5 — Translate Market Formation into CareFi Value")
st.markdown("""<div class="section-copy">The MEDUSDi / USDC pool is the operating proof point. It can turn CareFi’s initial float position into retained inventory value, LP fee economics, and evidence for a broader healthcare inflation infrastructure business.</div>""", unsafe_allow_html=True)

ev_components = pd.DataFrame([
    {"Component":"Inventory FV accretion","Value":max(inventory_accretion,0),"Explanation":"Discounted USDiMED float marked to medical-CPI fair value."},
    {"Component":"LP revenue value","Value":lp_revenue_value,"Explanation":"Annual CareFi LP fee revenue capitalized at the selected multiple."},
    {"Component":"Retained inventory FV","Value":retained_inventory_fv,"Explanation":"USDiMED retained after seeding the pool."},
])
ev_fig = go.Figure()
ev_fig.add_bar(x=ev_components["Component"], y=ev_components["Value"], text=[fmt_usd(v) for v in ev_components["Value"]], textposition="auto")
ev_fig.update_layout(title="Modeled CareFi value components", yaxis_title="USD", height=420, margin=dict(l=20, r=20, t=55, b=80))
st.plotly_chart(ev_fig, use_container_width=True)
st.dataframe(ev_components.assign(Value=ev_components["Value"].map(fmt_usd)), use_container_width=True, hide_index=True)

st.markdown(f"""
<div class="callout">
    <b>Strategic infrastructure upside is intentionally separated from the base modeled value.</b><br><br>
    The base model does not require investors to assign value to the full infrastructure opportunity. It first shows what can be observed: inventory acquired below fair value, MEDUSDi retained by CareFi, and LP economics created by the pool. The broader CareFi upside comes if that pool becomes a credible reference market for healthcare inflation exposure.<br><br>
    <b>Strategic upside not included in the base chart:</b><br>
    • live MEDUSDi / USDC price<br>
    • spot / fair-value basis<br>
    • trading-volume evidence<br>
    • future index and reference licensing<br>
    • structured-product and hedge-market optionality<br><br>
    Current strategic upside placeholder: <b>{fmt_usd(reference_option_value)}</b>
</div>
""", unsafe_allow_html=True)

st.subheader("Investor ownership lens")
o = st.columns(5)
o[0].metric("Investor check", fmt_usd(investor_check))
o[1].metric("Pre-money valuation", fmt_usd(pre_money))
o[2].metric("Investor ownership", fmt_pct(investor_ownership))
o[3].metric("Value from modeled EV accretion", fmt_usd(investor_value_from_accretion))
o[4].metric("Check coverage", f"{check_coverage:,.2f}x")

st.markdown("""<div class="callout"><b>Investor takeaway:</b> a MEDUSDi buyer owns the exposure. A CareFi investor owns the company positioned to acquire the initial discounted float, anchor the MEDUSDi / USDC market, earn LP economics, retain strategic inventory, and build the infrastructure layer around healthcare inflation and cost-risk pricing.</div>""", unsafe_allow_html=True)



st.header("What Drives CareFi Value?")
st.markdown("""<div class="section-copy">This sensitivity view shows which assumptions move modeled CareFi value most. It keeps the conversation focused on the drivers that matter: volume, LP share, revenue multiple, retained inventory, and acquisition basis.</div>""", unsafe_allow_html=True)

baseline_value = modeled_carefi_value
sensitivity_rows = []

drivers = [
    ("Monthly trading volume", monthly_volume * 0.5, monthly_volume * 1.5, "monthly_volume"),
    ("CareFi LP share", max(carefi_lp_share - 0.15, 0), min(carefi_lp_share + 0.15, 1), "carefi_lp_share"),
    ("LP revenue multiple", max(revenue_multiple - 3, 1), revenue_multiple + 3, "revenue_multiple"),
    ("Retained MEDUSDi inventory", retained_med * 0.75, retained_med * 1.25, "retained_med"),
    ("Acquisition price", max(acquisition_price - 0.03, 0), acquisition_price + 0.03, "acquisition_price"),
]

for label, low, high, key in drivers:
    kwargs_low = dict(monthly_volume_v=monthly_volume, carefi_lp_share_v=carefi_lp_share, revenue_multiple_v=revenue_multiple, retained_med_v=retained_med, acquisition_price_v=acquisition_price)
    kwargs_high = kwargs_low.copy()
    if key == "monthly_volume":
        kwargs_low["monthly_volume_v"] = low
        kwargs_high["monthly_volume_v"] = high
    elif key == "carefi_lp_share":
        kwargs_low["carefi_lp_share_v"] = low
        kwargs_high["carefi_lp_share_v"] = high
    elif key == "revenue_multiple":
        kwargs_low["revenue_multiple_v"] = low
        kwargs_high["revenue_multiple_v"] = high
    elif key == "retained_med":
        kwargs_low["retained_med_v"] = low
        kwargs_high["retained_med_v"] = high
    elif key == "acquisition_price":
        kwargs_low["acquisition_price_v"] = low
        kwargs_high["acquisition_price_v"] = high

    low_value = compute_modeled_value_for_sensitivity(**kwargs_low)
    high_value = compute_modeled_value_for_sensitivity(**kwargs_high)
    sensitivity_rows.append({"Driver": label, "Low case": low_value, "Base": baseline_value, "High case": high_value, "Range": abs(high_value - low_value)})

sens_df = pd.DataFrame(sensitivity_rows).sort_values("Range", ascending=True)

sens_fig = go.Figure()
sens_fig.add_bar(
    y=sens_df["Driver"],
    x=sens_df["High case"] - sens_df["Low case"],
    base=sens_df["Low case"],
    orientation="h",
    text=[f"{fmt_usd(lo)} → {fmt_usd(hi)}" for lo, hi in zip(sens_df["Low case"], sens_df["High case"])],
    textposition="auto",
)
sens_fig.add_vline(x=baseline_value, line_dash="dash", annotation_text="Base", annotation_position="top")
sens_fig.update_layout(
    title="Modeled value sensitivity by driver",
    xaxis_title="Modeled CareFi value",
    yaxis_title="",
    height=420,
    margin=dict(l=20, r=20, t=55, b=40),
)
st.plotly_chart(sens_fig, use_container_width=True)

sens_display = sens_df.sort_values("Range", ascending=False).copy()
for col in ["Low case", "Base", "High case", "Range"]:
    sens_display[col] = sens_display[col].map(fmt_usd)
st.dataframe(sens_display[["Driver", "Low case", "Base", "High case", "Range"]], use_container_width=True, hide_index=True)

st.markdown("""
<div class="callout">
    <b>Investor read-through:</b> the model should not hinge on the initial float discount alone. The larger drivers are whether the pool attracts volume, whether CareFi retains meaningful LP participation, and whether the spot market becomes credible enough to support infrastructure products.
</div>
""", unsafe_allow_html=True)

st.header("Investor FAQ")
st.markdown("""<div class="section-copy">Key questions about the float strategy, the MEDUSDi / USDC pool, and CareFi equity exposure.</div>""", unsafe_allow_html=True)

with st.expander("1. What is the difference between buying MEDUSDi and investing in CareFi?", expanded=False):
    st.write("Buying MEDUSDi gives direct exposure to medical-inflation-linked value through the token itself. Investing in CareFi gives exposure to the operating company building the market infrastructure around that exposure, including the initial float strategy, the MEDUSDi / USDC reference pool, LP economics retained by CareFi, retained inventory, data/reference products, and future healthcare cost-risk surfaces.")

with st.expander("2. Does a CareFi note or equity investor directly own the MEDUSDi / USDC pool?", expanded=False):
    st.write("Not automatically. CareFi note or equity investors own exposure to CareFi as the operating company. Any direct pool, SPV, sidecar, or warrant exposure would need to be structured separately and clearly documented. The model shows how the pool may contribute to CareFi enterprise value, but legal and economic entitlement depends on the offering structure.")

with st.expander("3. Does an investor in the MEDUSDi / USDC pool also own equity in CareFi?", expanded=False):
    st.write("Not automatically. An investment in a MEDUSDi / USDC pool, SPV, or sidecar would generally provide exposure to the pool economics defined in that vehicle — for example, MEDUSDi exposure, USDC-paired liquidity, LP fees, inventory appreciation or depreciation, and basis movement. CareFi equity is separate unless the offering expressly includes equity, a note, a warrant, or another contractual right to participate in CareFi.")

with st.expander("4. Could an investor receive both pool exposure and CareFi equity upside?", expanded=False):
    st.write("Yes, if structured intentionally. A combined note, sidecar, or warrant-linked structure could provide CareFi equity or equity-like upside plus direct or linked exposure to the MEDUSDi / USDC pool. If CareFi passes through USDiMED exposure, the buyer should expect the same transfer, liquidity, holding-period, and market-development limitations that apply to the underlying USDiMED allocation. The model shows both value engines, but actual entitlement depends on issuer consent, legal structure, and final documentation.")

with st.expander("5. Why does control of the initial USDiMED float matter?", expanded=False):
    st.write("Early float control gives CareFi the ability to seed the first external USDC-facing market from a position acquired at or below fair value. That creates a launch wedge: inventory accretion, market formation, price discovery, and potential LP economics before broader organic supply develops.")

with st.expander("6. How does the Uniswap-style pool create value?", expanded=False):
    st.write("The pool creates a visible USDC price for MEDUSDi, enables third-party trading, generates LP fees, and produces a spot/fair-value basis that can become useful for future reference products. The pool is the anchor proof point for the broader market infrastructure thesis.")

with st.expander("7. What happens when more USDi holders create their own MEDUSDi slices?", expanded=False):
    st.write("Additional slicing can expand supply and deepen the market. That may reduce CareFi's percentage share of total MEDUSDi supply over time, but it can also improve liquidity, credibility, and reference-market usefulness. CareFi's goal is not to permanently control all supply; it is to own the launch wedge and help form the market.")

with st.expander("8. Is the app assuming guaranteed trading volume or returns?", expanded=False):
    st.write("No. The model is illustrative. It lets investors test assumptions about float acquisition, pool formation, trading volume, LP fees, and CareFi enterprise-value accretion. It should not be read as a projection, guarantee, valuation opinion, or investment advice.")

with st.expander("9. Why would investors choose CareFi instead of just buying MEDUSDi?", expanded=False):
    st.write("MEDUSDi is the exposure. CareFi is the company positioned to build and monetize the market layer around that exposure. A CareFi investor may benefit from multiple engines: discounted inventory, anchor LP economics retained by CareFi, retained MEDUSDi exposure, reference-market credibility, and future infrastructure products around healthcare inflation and cost-risk pricing.")

with st.expander("10. What is the long-term infrastructure opportunity?", expanded=False):
    st.write("The MEDUSDi / USDC pool can become an early observable reference point for healthcare inflation exposure. From there, CareFi can build fair-value surfaces, basis analytics, listed contract support, structured products, data/reference licensing, and cost-risk tools for providers, payers, employers, reinsurers, and healthcare investors.")

st.markdown("""
<div class="section-copy" style="font-size:0.85rem; margin-top:1.5rem;">
    <b>Model limitation:</b> This app is illustrative and assumes future market development. USDiMED is a novel instrument with limited or no trading history. Secondary liquidity, split/recombine functionality, market-maker participation, and regulatory treatment are not guaranteed.
</div>
""", unsafe_allow_html=True)

st.caption("Illustrative scenario model only. This is not investment advice, a valuation opinion, a guarantee of liquidity, or a projection of returns.")
