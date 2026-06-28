import streamlit as st
import pandas as pd
import numpy as np

# 1. Basic Page Configuration (Bina kisi extra heavy tweaks ke)
st.set_page_config(page_title="KraveMart Simulator", layout="wide")

st.title("🎯 KraveMart Supply Chain Simulator")
st.text("Pure Native Engine — Anti-Freeze Minimalist Edition")

# ─────────────────────────────────────────
# CORE ENGINE
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

    bottleneck     = 'WH → Zone Last-Mile' if total_wh_cap < total_sh_cap else 'SH → WH Trunk'
    extra_wh       = int(np.ceil(deficit / wh_capacity)) if deficit > 0 else 0

    return dict(
        total_zones=total_zones, baseline_dem=baseline_dem,
        stressed_dem=stressed_dem, stress_flow=round(stress_flow), deficit=round(deficit),
        wh_util=wh_util, network_cap=round(network_cap), bottleneck=bottleneck,
        extra_wh=extra_wh, num_wh=num_wh, num_sh=num_sh, spike=spike,
        sh_capacity=round(num_sh * sh_capacity), wh_capacity=round(num_wh * wh_capacity)
    )

# ─────────────────────────────────────────
# SIDEBAR FILTER LAYER
# ─────────────────────────────────────────
st.sidebar.header("⚡ Demand Configurations")
spike_slider = st.sidebar.slider("Spike Factor (x)", 1.0, 3.0, 1.5, 0.1)
demand_slider = st.sidebar.slider("Zone Base Demand", 50, 800, 264, 10)
buffer_slider = st.sidebar.slider("Buffer Elasticity (%)", 0, 80, 0, 5)

st.sidebar.header("🏗️ Topology Setup")
num_wh_input = st.sidebar.number_input("Total Warehouses", 1, 12, 4)
num_sh_input = st.sidebar.number_input("Total Superhouses", 1, 6, 2)
zones_wh_input = st.sidebar.number_input("Zones per WH", 5, 100, 50)
wh_cap_input = st.sidebar.number_input("Single WH Cap", 1000, 50000, 14000, 500)
sh_cap_input = st.sidebar.number_input("Single SH Cap", 5000, 100000, 27000, 1000)

# Run Engine Calculations
r = compute(
    num_wh=num_wh_input, num_sh=num_sh_input, zones_per_wh=zones_wh_input,
    wh_cap=wh_cap_input, sh_cap=sh_cap_input, spike=spike_slider,
    avg_demand=demand_slider, buffer_pct=buffer_slider
)

# ─────────────────────────────────────────
# MAIN SCOREBOARD LAYER (Row by Row Placement)
# ─────────────────────────────────────────
st.subheader("📊 Network KPIs")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Baseline Load", f"{r['baseline_dem']:,}")
k2.metric("Stressed Peak", f"{r['stressed_dem']:,}")
k3.metric("Throughput Met", f"{r['stress_flow']:,}")
k4.metric("Network Deficit", f"{r['deficit']:,}")

st.markdown("---")

# ─────────────────────────────────────────
# DATA AND METRICS BREAKDOWN
# ─────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("📈 Capacity Logs")
    if r['wh_util'] > 100:
        st.error(f"⚠️ Critical Overload: {r['wh_util']:.1f}%")
    else:
        st.success(f"✅ Safe Run: {r['wh_util']:.1f}%")
        
    log_df = pd.DataFrame({
        "Metrics Target": ["Superhouse Capacity", "Warehouse Capacity", "Last-Mile Delivery Limit"],
        "Value (Orders/Day)": [f"{r['sh_capacity']:,}", f"{r['wh_capacity']:,}", f"{r['network_cap']:,}"]
    })
    st.table(log_df)

with col_r:
    st.subheader("⚡ Operational Breakdown Chart")
    chart_df = pd.DataFrame({
        "Orders Limit": [r['sh_capacity'], r['wh_capacity'], r['network_cap']]
    }, index=["Superhouses", "Warehouses", "Network Limit"])
    st.bar_chart(chart_df, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────
# RECOVERY ADVISORY
# ─────────────────────────────────────────
st.subheader("💡 Strategic Advisory")
if r['deficit'] == 0:
    st.info(f"System completely stable under {r['spike']}x promotion peak load.")
else:
    st.warning(f"Bottleneck alert at: **{r['bottleneck']}** layer. Recommended to deploy **{r['extra_wh']} more Warehouse point(s)**.")
