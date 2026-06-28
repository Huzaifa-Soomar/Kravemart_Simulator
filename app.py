import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')

# 1. Page Configuration for Maximum Screen Real Estate
st.set_page_config(page_title="KraveMart Logistics Simulator", layout="wide")

st.title("🚚 KraveMart Supply Chain Simulator")
st.caption("Responsive UI Production Engine — Scroll-Optimized Layout")

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
# 1. EXECUTIVE KPIS (Top Metrics Bar)
# ─────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Baseline Demand", f"{r['baseline_dem']:,} /day")
m2.metric(f"Stressed Load ({r['spike']}x)", f"{r['stressed_dem']:,} /day")
m3.metric("Max-Flow Met", f"{r['stress_flow']:,}", f"Deficit: {r['deficit']:,}", delta_color="inverse" if r['deficit'] > 0 else "normal")
m4.metric("Network Capacity Threshold", f"{r['network_cap']:,}", f"Bottleneck: {r['bottleneck']}", delta_color="off")

st.markdown("---")

# ─────────────────────────────────────────
# 2. TWO COLUMN ANALYTICS ROW (Prevents Page Overflow)
# ─────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Warehouse Capacity Stress")
    fig_wh, ax1 = plt.subplots(figsize=(6, 3.5))
    fig_wh.patch.set_facecolor('#f8f8f6')
    ax1.set_facecolor('white')
    
    num_wh = r['num_wh']
    wh_labels = [f'WH{i+1:02d}' for i in range(num_wh)]
    utils = [min(200, r['wh_util']) for _ in range(num_wh)]
    WH_COLORS = ['#2a78d6','#1baf7a','#eda100','#e34948','#4a3aa7','#eb6834','#e87ba4','#008300']
    cols = [('#e34948' if u > 100 else WH_COLORS[i % len(WH_COLORS)]) for i, u in enumerate(utils)]
    
    bars = ax1.barh(wh_labels, utils, color=cols, height=0.55)
    ax1.axvline(100, color='#e34948', linestyle='--', linewidth=1.2, label='100% Limit')
    ax1.set_xlim(0, max(220, max(utils)+20))
    ax1.set_xlabel('Utilisation %', fontsize=8)
    ax1.tick_params(axis='both', which='major', labelsize=8)
    ax1.legend(fontsize=7, loc='lower right')
    ax1.grid(axis='x', alpha=0.2)
    ax1.spines[['top','right','left']].set_visible(False)
    
    for bar, u in zip(bars, utils):
        ax1.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2, f'{u:.0f}%', va='center', fontsize=8, fontweight='bold')
        
    st.pyplot(fig_wh)

with col_right:
    st.subheader("✂️ Min-Cut Tier Diagnostics")
    fig_mc, ax2 = plt.subplots(figsize=(6, 3.5))
    fig_mc.patch.set_facecolor('#f8f8f6')
    ax2.set_facecolor('white')
    
    layer_names = ['SH Cap', 'WH Cap', 'Last-Mile Arcs']
    layer_caps  = [r['layers'][0][1], r['layers'][1][1], r['layers'][2][1]]
    is_min      = [c == r['min_layer_cap'] for c in layer_caps]
    bar_cols    = ['#e34948' if m else '#2a78d6' for m in is_min]
    
    xpos = np.arange(len(layer_names))
    b2 = ax2.bar(xpos, layer_caps, color=bar_cols, width=0.4)
    ax2.axhline(r['stressed_dem'], color='#eda100', linestyle='--', linewidth=1.2, label="Stressed Load")
    ax2.set_xticks(xpos)
    ax2.set_xticklabels(layer_names, fontsize=8)
    ax2.set_ylabel('Orders/Day', fontsize=8)
    ax2.tick_params(axis='both', which='major', labelsize=8)
    ax2.grid(axis='y', alpha=0.2)
    ax2.spines[['top','right','left']].set_visible(False)
    
    for bar, cap, m in zip(b2, layer_caps, is_min):
        ax2.text(bar.get_x()+bar.get_width()/2, cap + (max(layer_caps)*0.02), f'{cap:,}', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
    st.pyplot(fig_mc)

st.markdown("---")

# ─────────────────────────────────────────
# 3. BOTTOM ROW: SCHEMATIC AND ACTION PLAN
# ─────────────────────────────────────────
col_bot1, col_bot2 = st.columns([3, 2])

with col_bot1:
    st.subheader("🌐 Supply Network Topological Graph")
    fig_net, ax3 = plt.subplots(figsize=(7, 4))
    fig_net.patch.set_facecolor('#f8f8f6')
    ax3.set_facecolor('white')
    ax3.set_xlim(-0.5, 5); ax3.set_ylim(-0.5, max(4, num_wh)+0.5); ax3.axis('off')

    def draw_node(ax, x, y, txt, col, sz=900):
        ax.scatter(x, y, s=sz, c=col, zorder=3, edgecolors='white', linewidths=1.2)
        ax.text(x, y, txt, ha='center', va='center', fontsize=7, fontweight='bold', color='white', zorder=4)

    mid = max(4, num_wh) / 2
    num_sh = r['num_sh']
    sh_ys = np.linspace(0.5, max(4, num_wh)-0.5, num_sh)
    wh_ys = np.linspace(0.3, max(4, num_wh)-0.3, num_wh)
    whs_per_sh = int(np.ceil(num_wh / num_sh))
    is_wh_bn = 'WH' in r['bottleneck']

    draw_node(ax3, 0, mid, 'HQ', '#888780')
    for i, sy in enumerate(sh_ys):
        draw_node(ax3, 1.2, sy, f'SH{i+1}', '#e87ba4', 700)
        ax3.annotate('', xy=(1.1, sy), xytext=(0.15, mid), arrowprops=dict(arrowstyle='->', color='#2a78d6', lw=1.5))
        
    for i, wy in enumerate(wh_ys):
        shi = min(int(i / whs_per_sh), num_sh-1)
        col = '#e34948' if is_wh_bn else '#1baf7a'
        draw_node(ax3, 2.5, wy, f'WH{i+1}', '#2a78d6', 600)
        ax3.annotate('', xy=(2.4, wy), xytext=(1.3, sh_ys[shi]), arrowprops=dict(arrowstyle='->', color=col, lw=1.2))
        ax3.annotate('', xy=(3.6, mid), xytext=(2.6, wy), arrowprops=dict(arrowstyle='->', color=col, lw=0.8))
        
    draw_node(ax3, 3.7, mid, f'{r["total_zones"]}Z', '#1baf7a', 900)
    ax3.annotate('', xy=(4.6, mid), xytext=(3.85, mid), arrowprops=dict(arrowstyle='->', color='#888780', lw=1.5))
    draw_node(ax3, 4.7, mid, 'SINK', '#888780')
    
    st.pyplot(fig_net)

with col_bot2:
    st.subheader("💡 Strategic Operations Strategy")
    if r['deficit'] == 0:
        st.success(f"### SYSTEM HEALTHY\n\nThe logistics framework handles **{r['spike']}x** volume spikes smoothly without resource starvation.\n\n**Headroom Available:** {r['network_cap'] - r['stressed_dem']:,} orders/day.")
    else:
        st.error(f"### CRISIS OVERLOAD DETECTED\n\nSystem fails to route **{r['deficit']:,} orders/day** due to localized resource depletion at the **{r['bottleneck']}** layer.")
        st.markdown(f"""
        **Direct Infrastructure Mitigations:**
        * **Option 1 (Asset Expansion):** Deploy exactly **{r['extra_wh']} secondary mid-tier Warehouse facility(s)** inside affected node vectors.
        * **Option 2 (Throughput Surge):** Inject a **{round((r['spike']-1)*100)}% capacity scale** across existing active hubs.
        """)
