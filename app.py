import streamlit as st
import numpy as np
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="KraveMart Logistics Simulator", layout="wide")

st.title("🚚 KraveMart Supply Chain Simulator")
st.caption("Production Engine — Lightweight Native UI (Anti-Freeze Edition)")

# ─────────────────────────────────────────
# CORE COMPUTE ENGINE
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

    bottleneck     = 'WH → Zone (last-mile)' if total_wh_cap < total_sh_cap else 'SH → WH'
    
    extra_wh       = int(np.ceil(deficit / wh_capacity)) if deficit > 0 else 0

    return dict(
        total_zones=total_zones, baseline_dem=baseline_dem,
        stressed_dem=stressed_dem, stress_flow=round(stress_flow), deficit=round(deficit),
        wh_util=wh_util, network_cap=round(network_cap), bottleneck=bottleneck,
        extra_wh=extra_wh, num_wh=num_wh, num_sh=num_sh, spike=spike,
        sh_capacity=round(num_sh * sh_capacity), wh_capacity=round(num_wh * wh_capacity)
    )

# ─────────────────────────────────────────
# SIDEBAR CONTROLS
# ─────────────────────────────────────────
st.sidebar.header("🎛️ Demand Configurations")
spike_slider = st.sidebar.slider("Spike Multiplier (x)", min_value=1.0, max_value=3.0, value=1.5, step=0.1)
demand_slider = st.sidebar.slider("Zone Avg Demand (orders/day)", min_value=50, max_value=800, value=264, step=10)
buffer_slider = st.sidebar.slider("Buffer Capacity (%)", min_value=0, max_value=80, value=0, step=5)

st.sidebar.header("🏗️ Infrastructure Topology")
num_wh_input = st.sidebar.number_input("Number of Warehouses", min_value=1, max_value=12, value=4)
num_sh_input = st.sidebar.number_input("Number of Superhouses", min_value=1, max_value=6, value=2)
zones_wh_input = st.sidebar.number_input("Zones per Warehouse", min_value=5, max_value=100, value=50)
wh_cap_input = st.sidebar.number_input("WH Capacity (orders/day)", min_value=1000, max_value=50000, value=14000, step=500)
sh_cap_input = st.sidebar.number_input("SH Capacity (orders/day)", min_value=5000, max_value=100000, value=27000, step=1000)

# Run computations
r = compute(
    num_wh=num_wh_input, num_sh=num_sh_input, zones_per_wh=zones_wh_input,
    wh_cap=wh_cap_input, sh_cap=sh_cap_input, spike=spike_slider,
    avg_demand=demand_slider, buffer_pct=buffer_slider
)

# ─────────────────────────────────────────
# 1. EXECUTIVE METRICS BAR
# ─────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Baseline Demand", f"{r['baseline_dem']:,} /day")
m2.metric(f"Stressed Load ({r['spike']}x)", f"{r['stressed_dem']:,} /day")
m3.metric("Max-Flow Met", f"{r['stress_flow']:,}", f"Deficit: {r['deficit']:,}", delta_color="inverse" if r['deficit'] > 0 else "normal")
m4.metric("Network Capacity", f"{r['network_cap']:,}", f"Bottleneck: {r['bottleneck']}", delta_color="off")

st.markdown("---")

# ─────────────────────────────────────────
# 2. LIGHTWEIGHT NATIVE UI CARDS
# ─────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Warehouse Capacity Utilisation")
    # Native clean Progress bar
    util_val = r['wh_util'] / 100.0
    if util_val > 1.0:
        st.error(f"⚠️ Warehouses are Overloaded! Utilisation: {r['wh_util']:.1f}%")
        st.progress(1.0)
    else:
        st.success(f"📈 Warehouses Operating Safely. Utilisation: {r['wh_util']:.1f}%")
        st.progress(util_val)
        
    # Quick Table Preview instead of broken heavy graphs
    wh_data = pd.DataFrame({
        "Warehouse Hub": [f"WH {i+1:02d}" for i in range(r['num_wh'])],
        "Utilisation Rate": [f"{r['wh_util']:.1f}%" for _ in range(r['num_wh'])],
        "Status": ["OVERLOAD" if r['wh_util'] > 100 else "HEALTHY" for _ in range(r['num_wh'])]
    })
    st.dataframe(wh_data, use_container_width=True, hide_index=True)

with col_right:
    st.subheader("✂️ Network Tier Capacities")
    # Streamlit native responsive bar chart (No freeze, handles scaling perfectly)
    chart_data = pd.DataFrame(
        [r['sh_capacity'], r['wh_capacity'], r['network_cap']],
        index=['Superhouse Total Cap', 'Warehouse Total Cap', 'Last-Mile Route Cap'],
        columns=['Orders per Day']
    )
    st.bar_chart(chart_data, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────
# 3. BOTTOM ROW: ACTION PLAN & RECOMMENDATIONS
# ─────────────────────────────────────────
st.subheader("💡 Strategic Operations Advice")
if r['deficit'] == 0:
    st.success(f"### Everything is working perfectly!\n\nThe network can successfully handle the current **{r['spike']}x** load without breaking down.")
else:
    st.error(f"### 🚨 Bottleneck Alert at {r['bottleneck']} Layer")
    st.markdown(f"""
    **Immediate Action Steps Required:**
    1. **Expand Fleet:** Add at least **{r['extra_wh']} more temporary warehouse routing hubs** to absorb the remaining **{r['deficit']:,} unfulfilled orders**.
    2. **Surge Staffing:** Increase the buffer capacity configuration in the sidebar to dynamically upgrade active nodes.
    """)
