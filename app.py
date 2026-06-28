import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# Page Configuration
st.set_page_config(page_title="KraveMart Supply Chain Simulator", layout="wide")

st.title("🚚 KraveMart Interactive Supply Chain Simulator")
st.caption("Native Streamlit Deployment Engine — Production Ready")

# ─────────────────────────────────────────
# CORE COMPUTE ENGINE
# ─────────────────────────────────────────
def compute(num_wh, num_sh, zones_per_wh, wh_cap, sh_cap,
            spike, avg_demand, buffer_pct):

    total_zones    = num_wh * zones_per_wh
    baseline_dem   = total_zones * avg_demand
    stressed_dem   = round(baseline_dem * spike)

    wh_capacity    = wh_cap * (1 + buffer_pct / 100)
    sh_capacity    = sh_cap * (1 + buffer_pct / 100)
    whs_per_sh     = int(np.ceil(num_wh / num_sh))

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

# ─────────────────────────────────────────
# STREAMLIT SIDEBAR CONTROLS (Replacing ipywidgets)
# ─────────────────────────────────────────
st.sidebar.header("🎛️ Demand Controls")
spike_slider = st.sidebar.slider("Spike Multiplier (x)", min_value=1.0, max_value=3.0, value=1.5, step=0.1)
demand_slider = st.sidebar.slider("Zone Avg Demand (orders/day)", min_value=50, max_value=800, value=264, step=10)
buffer_slider = st.sidebar.slider("Buffer Capacity (%)", min_value=0, max_value=80, value=0, step=5)

st.sidebar.header("🏗️ Infrastructure Settings")
num_wh_input = st.sidebar.number_input("Number of Warehouses", min_value=1, max_value=12, value=4)
num_sh_input = st.sidebar.number_input("Number of Superhouses", min_value=1, max_value=6, value=2)
zones_wh_input = st.sidebar.number_input("Zones per Warehouse", min_value=5, max_value=100, value=50)
wh_cap_input = st.sidebar.number_input("WH Capacity (orders/day)", min_value=1000, max_value=50000, value=14000, step=500)
sh_cap_input = st.sidebar.number_input("SH Capacity (orders/day)", min_value=5000, max_value=100000, value=27000, step=1000)

# Trigger calculation dynamically
r = compute(
    num_wh=num_wh_input, num_sh=num_sh_input, zones_per_wh=zones_wh_input,
    wh_cap=wh_cap_input, sh_cap=sh_cap_input, spike=spike_slider,
    avg_demand=demand_slider, buffer_pct=buffer_slider
)

# ─────────────────────────────────────────
# DYNAMIC NATIVE STREAMLIT METRIC CARDS
# ─────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Baseline Demand", value=f"{r['baseline_dem']:,} orders/day")
col2.metric(label=f"Stressed Demand ({r['spike']}x)", value=f"{r['stressed_dem']:,} orders/day")

status_txt = "🟢 FULLY MET" if r['deficit'] == 0 else f"🔴 DEFICIT: {r['deficit']:,}"
col3.metric(label="Max-Flow Achieved", value=f"{r['stress_flow']:,}", delta=status_txt, delta_color="normal")
col4.metric(label="Network Capacity", value=f"{r['network_cap']:,}", delta=r['bottleneck'], delta_color="inverse")

st.markdown("---")

# ─────────────────────────────────────────
# PLOTTING CHART LAYOUT ENGINE
# ─────────────────────────────────────────
WH_COLORS = ['#2a78d6','#1baf7a','#eda100','#e34948','#4a3aa7','#eb6834','#e87ba4','#008300','#888780','#534AB7','#D85A30','#0F6E56']

fig = plt.figure(figsize=(15, 9))
fig.patch.set_facecolor('#f8f8f6')
gs = GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.3)

# Bar 1: WH Utilisation Under Stress
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor('white')
ax1.set_title('Warehouse utilisation under stress', fontsize=11, pad=8, color='#3d3d3a', fontweight='bold')
num_wh = r['num_wh']
wh_labels = [f'WH{i+1:02d}' for i in range(num_wh)]
utils = [min(200, r['wh_util']) for _ in range(num_wh)]
cols = [('#e34948' if u > 100 else WH_COLORS[i % len(WH_COLORS)]) for i, u in enumerate(utils)]
bars = ax1.barh(wh_labels, utils, color=cols, height=0.55)
ax1.axvline(100, color='#e34948', linestyle='--', linewidth=1.2, label='100% capacity')
ax1.set_xlim(0, max(220, max(utils)+20))
ax1.set_xlabel('Utilisation %', fontsize=9)
ax1.legend(fontsize=8)
for bar, u in zip(bars, utils):
    ax1.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, f'{u:.0f}%', va='center', fontsize=8)
ax1.grid(axis='x', alpha=0.3)
ax1.spines[['top','right','left']].set_visible(False)

# Bar 2: Min-Cut Layer Chart
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor('white')
ax2.set_title('Min-cut analysis by layer', fontsize=11, pad=8, color='#3d3d3a', fontweight='bold')
layer_names = [l[0] for l in r['layers']]
layer_caps  = [l[1] for l in r['layers']]
is_min      = [c == r['min_layer_cap'] for c in layer_caps]
bar_cols    = ['#e34948' if m else '#2a78d6' for m in is_min]
xpos        = np.arange(len(layer_names))
b2 = ax2.bar(xpos, layer_caps, color=bar_cols, width=0.4)
ax2.axhline(r['stressed_dem'], color='#eda100', linestyle='--', linewidth=1.2, label=f"Stressed demand")
ax2.set_xticks(xpos)
ax2.set_xticklabels(layer_names, fontsize=8)
ax2.set_ylabel('Capacity (orders/day)', fontsize=9)
for bar, cap, m in zip(b2, layer_caps, is_min):
    ax2.text(bar.get_x()+bar.get_width()/2, cap+500, f'{cap:,}', ha='center', va='bottom', fontsize=8, fontweight='bold' if m else 'normal')
patch_min = mpatches.Patch(color='#e34948', label='Min-cut (bottleneck)')
patch_ok  = mpatches.Patch(color='#2a78d6', label='OK')
ax2.legend(handles=[patch_min, patch_ok], fontsize=8, loc='upper right')
ax2.grid(axis='y', alpha=0.3)
ax2.spines[['top','right','left']].set_visible(False)

# Graph 3: Flow Schematic Network
ax3 = fig.add_subplot(gs[1, 0])
ax3.set_facecolor('white')
ax3.set_title('Flow network schematic', fontsize=11, pad=8, color='#3d3d3a', fontweight='bold')
ax3.set_xlim(-0.5, 5); ax3.set_ylim(-0.5, num_wh+0.5); ax3.axis('off')

def draw_node(ax, x, y, txt, col, sz=1200):
    ax.scatter(x, y, s=sz, c=col, zorder=3, edgecolors='white', linewidths=1.5)
    ax.text(x, y, txt, ha='center', va='center', fontsize=7.5, fontweight='bold', color='white', zorder=4)

mid = num_wh / 2
num_sh = r['num_sh']
sh_ys = np.linspace(0.5, num_wh-0.5, num_sh)
wh_ys = np.linspace(0.3, num_wh-0.3, num_wh)
whs_per_sh = int(np.ceil(num_wh / num_sh))
is_wh_bn = 'WH' in r['bottleneck']

draw_node(ax3, 0, mid, 'HQ', '#888780')
for i, sy in enumerate(sh_ys):
    draw_node(ax3, 1.2, sy, f'SH{i+1}', '#e87ba4', 800)
    ax3.annotate('', xy=(1.05, sy), xytext=(0.2, mid), arrowprops=dict(arrowstyle='->', color='#2a78d6', lw=2))
for i, wy in enumerate(wh_ys):
    shi = min(int(i / whs_per_sh), num_sh-1)
    col = '#e34948' if is_wh_bn else WH_COLORS[i % len(WH_COLORS)]
    draw_node(ax3, 2.5, wy, f'WH{i+1}', WH_COLORS[i % len(WH_COLORS)], 700)
    ax3.annotate('', xy=(2.3, wy), xytext=(1.4, sh_ys[shi]), arrowprops=dict(arrowstyle='->', color=col, lw=1.5))
    ax3.annotate('', xy=(3.4, mid), xytext=(2.7, wy), arrowprops=dict(arrowstyle='->', color=col, lw=0.8))
draw_node(ax3, 3.7, mid, f'{r["total_zones"]}Z', '#1baf7a', 1100)
ax3.annotate('', xy=(4.6, mid), xytext=(4.0, mid), arrowprops=dict(arrowstyle='->', color='#888780', lw=2))
draw_node(ax3, 4.8, mid, 'SINK', '#888780')

ax3.text(2.5, -0.3, f"Baseline: {r['base_flow']:,} | Stressed: {r['stress_flow']:,}", ha='center', fontsize=9, fontweight='bold')

# Inject Matplotlib chart into Streamlit layout
st.pyplot(fig)

# ─────────────────────────────────────────
# RECOMMENDATIONS AREA
# ─────────────────────────────────────────
st.subheader("💡 Optimization Recommendations")
if r['deficit'] == 0:
    st.success(f"Network is HEALTHY at {r['spike']}x load! Capacity headroom: {r['network_cap'] - r['stressed_dem']:,} orders/day")
else:
    st.error(f"OVERLOADED at {r['spike']}x demand! Bottleneck identified at: {r['bottleneck']}")
    st.warning(f"**Action Plan Proposals:**\n"
               f"* **Option A:** Setup/Deploy at least **{r['extra_wh']} new local warehouse infrastructure point(s)**.\n"
               f"* **Option B:** Upgrade existing active fulfillment center limits by **{round((r['spike']-1)*100)}%** immediately to bypass structural min-cuts.")
