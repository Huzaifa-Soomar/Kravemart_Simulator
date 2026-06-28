import streamlit as st
import pandas as pd
import numpy as np

# 1. Wide Layout Setup with Modern Theme
st.set_page_config(
    page_title="KraveMart Control Room", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom Glassmorphism UI Tweak to fix scrolling freeze forever
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 24px !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 KraveMart Supply Chain Simulation Hub")
st.caption("Active Sandbox Architecture — Fully Scrollable Core")

# ─────────────────────────────────────────
# CORE ENGINE (Bina kisi notebook dependencies ke)
# ─────────────────────────────────────────
def compute(num_wh, num_sh, zones_per_wh, wh_cap, sh_cap, spike, avg_demand, buffer_pct):
    total_zones    = num_wh * zones_per_wh
    baseline_dem   = total_zones * avg_demand
    stressed_dem   = round(baseline_dem * spike)

    wh_capacity    = wh_cap * (1 + buffer_pct / 100)
    sh_capacity    = sh_cap * (1 + buffer_pct / 100)

    total_wh_cap   = wh_capacity * num_wh
    total_sh_cap   = sh_capacity * num_sh
    network_cap    = min(total_wh_cap, total_sh_cap)

    stress_flow    = min(network_cap, stressed_dem)
    deficit        = max(0, stressed_dem - stress_flow)

    stress_per_wh  = stressed_dem / num_wh
    wh_util        = min(200.0, (stress_per_wh / wh_capacity) * 100)

    bottleneck     = 'WH → Zone Last-Mile' if total_wh_cap < total_sh_cap else 'SH → WH Core Trunk'
    extra_wh       = int(np.ceil(deficit / wh_capacity)) if deficit > 0 else 0

    return dict(
        total_zones=total_zones, baseline_dem=baseline_dem,
        stressed_dem=stressed_dem, stress_flow=round(stress_flow), deficit=round(deficit),
        wh_util=wh_util, network_cap=round(network_cap), bottleneck=bottleneck,
        extra_wh=extra_wh, num_wh=num_wh, num_sh=num_sh, spike=spike,
        sh_capacity=round(num_sh * sh_capacity), wh_capacity=round(num_wh * wh_capacity)
    )

# ─────────────────────────────────────────
# SIDEBAR CONTROLS (Replacing messy UI)
# ─────────────────────────────────────────
with st.sidebar:
    st.header("⚡ Operational Controls")
    spike_slider = st.slider("Spike Factor (x Multiplier)", 1.0, 3.0, 1.5, 0.1)
    demand_slider = st.slider("Zone Base Demand (orders/day)", 50, 800, 264, 10)
    buffer_slider = st.slider("Buffer Overhead Elasticity (%)", 0, 80, 0, 5)

    st.header("🏗️ Core Topology Setup")
    num_wh_input = st.number_input("Total Warehouses (Nodes)", 1, 12, 4)
    num_sh_input = st.number_input("Total Superhouses (Hubs)", 1, 6, 2)
    zones_wh_input = st.number_input("Zones Served per Warehouse", 5, 100, 50)
    wh_cap_input = st.number_input("Single WH Cap / Day", 1000, 50000, 14000, 500)
    sh_cap_input = st.number_input("Single SH Cap / Day", 5000, 100000, 27000, 1000)

# Compute current state
r = compute(
    num_wh=num_wh_input, num_sh=num_sh_input, zones_per_wh=zones_wh_input,
    wh_cap=wh_cap_input, sh_cap=sh_cap_input, spike=spike_slider,
    avg_demand=demand_slider, buffer_pct=buffer_slider
)

# ─────────────────────────────────────────
# MAIN LIVE VIEW: SCOREBOARD LAYER
# ─────────────────────────────────────────
st.subheader("📊 Network Scoreboard")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(label="Baseline System Load", value=f"{r['baseline_dem']:,} orders")
with kpi2:
    st.metric(label="Stressed Demand Peak", value=f"{r['stressed_dem']:,} orders")
with kpi3:
    status_msg = "🟢 Perfect Routing" if r['deficit'] == 0 else f"🚨 Deficit: {r['deficit']:,}"
    st.metric(label="Throughput Achieved", value=f"{r['stress_flow']:,}", delta=status_msg, delta_color="normal" if r['deficit'] == 0 else "inverse")
with kpi4:
    st.metric(label="Total Network Capacity", value=f"{r['network_cap']:,}", delta=f"Critical: {r['bottleneck']}", delta_color="off")

st.markdown("---")

# ─────────────────────────────────────────
# MODERN INTERACTIVE BLOCK LAYER
# ─────────────────────────────────────────
layout_left, layout_right = st.columns([1, 1])

with layout_left:
    st.subheader("📈 Warehouse Utilization Monitor")
    
    # Clean UI progress visualization
    current_util = r['wh_util']
    if current_util > 100:
        st.error(f"⚠️ Critical Overload Detected: {current_util:.1f}% Capacity Utilized")
    else:
        st.success(f"✅ Safe Operating Threshold: {current_util:.1f}% Utilized")
        
    # Interactive Table (No layout breaking)
    node_breakdown = pd.DataFrame({
        "Facility Vector": [f"Warehouse Hub {i+1:02d}" for i in range(r['num_wh'])],
        "Stress Load Rate": [f"{current_util:.1f}%" for _ in range(r['num_wh'])],
        "Operational Health": ["CRITICAL BREAK" if current_util > 100 else "OPTIMAL RUN" for _ in range(r['num_wh'])]
    })
    st.dataframe(node_breakdown, use_container_width=True, hide_index=True)

with layout_right:
    st.subheader("⚡ Capacity Distribution Chart")
    
    # Modern native responsive chart (Fluid width, zero layout freezes)
    distribution_metrics = pd.DataFrame({
        "Capacity Limit": [r['sh_capacity'], r['wh_capacity'], r['network_cap']],
    }, index=['Total Superhouse Tier', 'Total Warehouse Tier', 'Last-Mile Delivery Cap'])
    
    st.bar_chart(distribution_metrics, use_container_width=True, color="#2b6cb0")

st.markdown("---")

# ─────────────────────────────────────────
# BOTTOM LAYER: SIMULATOR ADVISORY
# ─────────────────────────────────────────
st.subheader("💡 Sandbox Strategic Advisory")
if r['deficit'] == 0:
    st.balloons()
    st.success(f"### Optimal Strategy Confirmed!\n\nYour selected infrastructure topology can successfully absorb the **{r['spike']}x** promotional spike. No structural changes are needed.")
else:
    st.error(f"### 🛑 Supply Chain Fracture Alert!")
    st.markdown(f"""
    **Algorithmic Fix Proposals to restore Equilibrium:**
    * **Action Item 1:** Deploy **{r['extra_wh']} more standalone Warehouse(s)** to scale up the local fulfillment limits.
    * **Action Item 2:** Increase the **Overhead Elasticity (Buffer %)** slider in the sidebar by at least **{int(r['wh_util'] - 100)}%** to simulate surge labor allocation.
    """)
