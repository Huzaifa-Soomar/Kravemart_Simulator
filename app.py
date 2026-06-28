import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')

# Set page configuration to wide mode
st.set_facecolor = None
st.set_page_config(page_title="KraveMart Supply Chain Simulator", layout="wide")

# ==========================================
# 1. CORE COMPUTE ENGINE
# ==========================================
def compute(num_wh, num_sh, zones_per_wh, wh_cap, sh_cap, spike, avg_demand, buffer_pct):
    total_zones    = num_wh * zones_per_wh
    baseline_dem   = total_zones * avg_demand
    stressed_dem   = round(baseline_dem * spike)

    wh_capacity    = wh_cap * (1 + buffer_pct / 100)
    sh_capacity    = sh_cap * (1 + buffer_pct / 100)

    total_wh_cap   = wh_capacity * num_wh
    total_sh_cap   = sh_capacity * num_sh
    network_cap    = min(total_wh_cap, total_sh_cap)

    base_flow      = min(network_cap, baseline_dem)
    stress_flow    = min(network_cap, stressed_dem)
    deficit        = max(0, stressed_dem - stress_flow)

    stress_per_wh  = stressed_dem / num_wh
    wh_util        = min(200, (stress_per_wh / wh_capacity) * 100)

    bottleneck     = 'WH → Zone (last-mile)' if total_wh_cap < total_sh_cap else 'SH → WH'
    min_cut_cap    = round(min(total_wh_cap, total_sh_cap))

    extra_wh       = int(np.ceil(deficit / wh_capacity)) if deficit > 0 else 0
    extra_sh       = int(np.ceil(deficit / sh_capacity)) if deficit > 0 else 0

    layers = [
        ('SOURCE → Superhouses',       round(num_sh * sh_capacity)),
        ('Superhouses → Warehouses',   round(num_wh * wh_capacity)),
        ('Warehouses → Zones',         min_cut_cap),
    ]
    min_layer_cap = min(v for _, v in layers)

    return dict(
        total_zones=total_zones, baseline_dem=baseline_dem,
        stressed_dem=stressed_dem, base_flow=round(base_flow),
        stress_flow=round(stress_flow), deficit=round(deficit),
        stress_per_wh=stress_per_wh, wh_util=wh_util,
        wh_capacity=wh_capacity, sh_capacity=sh_capacity,
        bottleneck=bottleneck, min_cut_cap=min_cut_cap,
        network_cap=round(network_cap),
        extra_wh=extra_wh, extra_sh=extra_sh,
        layers=layers, min_layer_cap=min_layer_cap,
        num_wh=num_wh, num_sh=num_sh, spike=spike,
        avg_demand=avg_demand, buffer_pct=buffer_pct,
        zones_per_wh=zones_per_wh,
    )

# ==========================================
# 2. STREAMLIT SIDEBAR (CONTROLS)
# ==========================================
st.sidebar.markdown("## 📊 Demand Controls")
spike = st.sidebar.slider("Spike Multiplier (x)", 1.0, 3.0, 1.5, step=0.1)
avg_demand = st.sidebar.slider("Zone Avg Demand (orders/day)", 50, 800, 264, step=10)
buffer_pct = st.sidebar.slider("Buffer Capacity (%)", 0, 80, 0, step=5)

st.sidebar.markdown("---")
st.sidebar.markdown("## 🏢 Infrastructure Settings")
num_wh = st.sidebar.number_input("Number of Warehouses", 1, 12, 4)
num_sh = st.sidebar.number_input("Number of Superhouses", 1, 6, 2)
zones_per_wh = st.sidebar.number_input("Zones per Warehouse", 5, 100, 50)
wh_cap = st.sidebar.number_input("WH Capacity (orders/day)", 1000, 50000, 14000, step=500)
sh_cap = st.sidebar.number_input("SH Capacity (orders/day)", 5000, 100000, 27000, step=1000)

# Run calculation engine
r = compute(num_wh, num_sh, zones_per_wh, wh_cap, sh_cap, spike, avg_demand, buffer_pct)

# ==========================================
# 3. STREAMLIT MAIN DASHBOARD LAYOUT
# ==========================================
st.title("🚀 KraveMart Interactive Supply Chain Simulator")
st.markdown("Stress test and model logistic resilience for Karachi networks in real-time.")
st.write("---")

# Row 1: KPI Scorecard Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Baseline Demand", value=f"{r['baseline_dem']:,} orders/day")
col2.metric(label=f"Stressed Demand ({r['spike']}x)", value=f"{r['stressed_dem']:,} orders/day")

status_txt = "🟢 FULLY MET" if r['deficit'] == 0 else f"🔴 DEFICIT: {r['deficit']:,}"
col3.metric(label="Max-Flow Achieved", value=f"{r['stress_flow']:,} orders/day", delta=status_txt, delta_color="normal" if r['deficit'] == 0 else "inverse")
col4.metric(label="Network Capacity Limit", value=f"{r['network_cap']:,} orders/day", delta=f"Limit: {r['bottleneck']}", delta_color="off")

st.write("---")

# Row 2: Two Column Layout for Metrics
graph_col1, graph_col2 = st.columns(2)
WH_COLORS = ['#2a78d6','#1baf7a','#eda100','#e34948','#4a3aa7','#eb6834','#e87ba4','#008300']

with graph_col1:
    st.subheader("Warehouse Utilisation Under Stress")
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    wh_labels = [f'WH{i+1:02d}' for i in range(r['num_wh'])]
    utils = [min(200, r['wh_util']) for _ in range(r['num_wh'])]
    cols = [('#e34948' if u > 100 else WH_COLORS[i % len(WH_COLORS)]) for i, u in enumerate(utils)]
    bars = ax1.barh(wh_labels, utils, color=cols, height=0.55)
    ax1.axvline(100, color='#e34948', linestyle='--', linewidth=1.2, label='100% Capacity')
    ax1.set_xlim(0, max(220, max(utils)+20))
    ax1.set_xlabel('Utilisation %')
    ax1.legend(loc='lower right')
    for bar, u in zip(bars, utils):
        ax1.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, f'{u:.0f}%', va='center', fontsize=8)
    ax1.grid(axis='x', alpha=0.3)
    st.pyplot(fig1)

with graph_col2:
    st.subheader("Min-Cut Capacity Analysis by Tier")
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    layer_names = [l[0] for l in r['layers']]
    layer_caps  = [l[1] for l in r['layers']]
    is_min      = [c == r['min_layer_cap'] for c in layer_caps]
    bar_cols    = ['#e34948' if m else '#2a78d6' for m in is_min]
    xpos        = np.arange(len(layer_names))
    b2 = ax2.bar(xpos, layer_caps, color=bar_cols, width=0.4)
    ax2.axhline(r['stressed_dem'], color='#eda100', linestyle='--', label=f"Stressed Demand")
    ax2.set_xticks(xpos)
    ax2.set_xticklabels(['SH Cap', 'WH Cap', 'Zone Cap'], rotation=0)
    for bar, 'cap', m in zip(b2, layer_caps, is_min):
        ax2.text(bar.get_x()+bar.get_width()/2, cap+500, f'{cap:,}', ha='center', fontsize=8, fontweight='bold' if m else 'normal')
    patch_min = mpatches.Patch(color='#e34948', label='Min-Cut Bottleneck')
    patch_ok  = mpatches.Patch(color='#2a78d6', label='Sufficient Capacity')
    ax2.legend(handles=[patch_min, patch_ok, mpatches.Patch(color='#eda100', label='Stressed Demand')], loc='lower left')
    ax2.grid(axis='y', alpha=0.3)
    st.pyplot(fig2)

# Row 3: Network Map Diagram
st.write("---")
st.subheader("Functional Graph Flow Network Routing Map")

fig3, ax3 = plt.subplots(figsize=(12, 4))
ax3.set_xlim(-0.5, 5); ax3.set_ylim(-0.5, r['num_wh']+0.5); ax3.axis('off')

def draw_node(ax, x, y, txt, col, sz=1200):
    ax.scatter(x, y, s=sz, c=col, zorder=3, edgecolors='white', linewidths=1.5)
    ax.text(x, y, txt, ha='center', va='center', fontsize=8, fontweight='bold', color='white', zorder=4)

mid = r['num_wh'] / 2
sh_ys = np.linspace(0.5, r['num_wh']-0.5, r['num_sh'])
wh_ys = np.linspace(0.3, r['num_wh']-0.3, r['num_wh'])
whs_per_sh = int(np.ceil(r['num_wh'] / r['num_sh']))
is_wh_bn = 'WH' in r['bottleneck']

draw_node(ax3, 0, mid, 'HQ', '#888780')
for i, sy in enumerate(sh_ys):
    draw_node(ax3, 1.2, sy, f'SH{i+1}', '#e87ba4', 800)
    ax3.annotate('', xy=(1.05, sy), xytext=(0.2, mid), arrowprops=dict(arrowstyle='->', color='#2a78d6', lw=2))
for i, wy in enumerate(wh_ys):
    shi = min(int(i / whs_per_sh), r['num_sh']-1)
    col = '#e34948' if is_wh_bn else WH_COLORS[i % len(WH_COLORS)]
    draw_node(ax3, 2.5, wy, f'WH{i+1}', WH_COLORS[i % len(WH_COLORS)], 700)
    ax3.annotate('', xy=(2.3, wy), xytext=(1.4, sh_ys[shi]), arrowprops=dict(arrowstyle='->', color=col, lw=1.5))
    ax3.annotate('', xy=(3.4, mid), xytext=(2.7, wy), arrowprops=dict(arrowstyle='->', color=col, lw=0.8))
draw_node(ax3, 3.7, mid, f'{r["total_zones"]}Z', '#1baf7a', 1100)
ax3.annotate('', xy=(4.6, mid), xytext=(4.0, mid), arrowprops=dict(arrowstyle='->', color='#888780', lw=2))
draw_node(ax3, 4.8, mid, 'SINK', '#888780')

st.pyplot(fig3)

# Row 4: Actionable Recommendation Banner
st.write("---")
st.subheader("💡 Strategic Optimization Infrastructure Recommendations")
if r['deficit'] == 0:
    st.success(f"### 🎉 Network Healthy!\nThe logistics infrastructure comfortably absorbs the {r['spike']}x holiday surge with a residual headroom capacity of **{r['network_cap'] - r['stressed_dem']:,} orders/day**.")
else:
    st.error(f"### ⚠️ System Failure Deficit Captured: {r['deficit']:,} orders/day\n"
             f"**Identified Infrastructure Bottleneck:** `{r['bottleneck']}` \n\n"
             f"To prevent lost order volume under this structural workload stress, implement one of these fixes:\n"
             f"* **Action A:** Allocate and construct an additional **{r['extra_wh']} hyper-local warehouses** inside failing regions.\n"
             f"* **Action B:** Scale structural capacity buffers on nodes up by **{round((r['spike']-1)*100)}%** prior to promotional launch windows.")
