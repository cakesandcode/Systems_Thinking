"""Chip-to-Rack Thermal Framing — Interactive Parametric Calculator.

Streamlit app that computes the thermal resistance chain from GPU junction
to ambient, comparing cold plate technologies across GPU configurations.
"""

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.thermal import (
    COLD_PLATE_CONFIGS,
    GPU_CONFIGS,
    ThermalConfig,
    ThermalResults,
    compute_thermal_chain,
)

# --- Page Config ---
st.set_page_config(
    page_title="Chip-to-Rack Thermal Framing",
    page_icon="🌡️",
    layout="wide",
)

st.title("Chip-to-Rack Thermal Framing")
st.caption(
    "Parametric thermal resistance chain calculator — "
    "based on West's problem-level localisation framework"
)

# --- Sidebar Inputs ---
st.sidebar.header("Configuration")

gpu_options = {v["label"]: k for k, v in GPU_CONFIGS.items()}
gpu_label = st.sidebar.selectbox("GPU", list(gpu_options.keys()), index=2)
gpu_key = gpu_options[gpu_label]

enabled_plates = {
    k: v for k, v in COLD_PLATE_CONFIGS.items() if v["enabled"]
}
disabled_plates = {
    k: v for k, v in COLD_PLATE_CONFIGS.items() if not v["enabled"]
}

cp_options = {v["label"]: k for k, v in enabled_plates.items()}
cp_label = st.sidebar.selectbox("Cold Plate", list(cp_options.keys()), index=0)
cp_key = cp_options[cp_label]

# Show disabled options as grayed-out info
if disabled_plates:
    for k, v in disabled_plates.items():
        st.sidebar.caption(f"~~{v['label']}~~ — data not comparable")

st.sidebar.divider()
st.sidebar.subheader("Thermal Parameters")

t_in = st.sidebar.slider(
    "Coolant Inlet T_in (°C)",
    min_value=20.0, max_value=60.0, value=40.0, step=1.0,
    help="ASHRAE W4 = 40°C",
)
t_j_limit = st.sidebar.slider(
    "Junction Limit T_j,max (°C)",
    min_value=80.0, max_value=105.0, value=90.0, step=1.0,
    help="NVIDIA spec: ~90°C",
)

st.sidebar.divider()
st.sidebar.subheader("Resistance Overrides")

r1_die = st.sidebar.number_input(
    "R₁ Die Bulk (K/W)", value=0.008, format="%.4f", step=0.001,
)
r4_manifold = st.sidebar.number_input(
    "R₄ Manifold (K/W)", value=0.005, format="%.4f", step=0.001,
)
r5_cdu = st.sidebar.number_input(
    "R₅ CDU (K/W)", value=0.0003, format="%.4f", step=0.0001,
)

st.sidebar.divider()
st.sidebar.subheader("Rack Parameters")

flow_starvation = st.sidebar.slider(
    "Flow Starvation (%)", min_value=0.0, max_value=50.0, value=30.0, step=5.0,
)
cdu_drift = st.sidebar.slider(
    "CDU Drift (°C)", min_value=0.0, max_value=15.0, value=3.0, step=1.0,
)

# --- Compute ---
config = ThermalConfig(
    gpu=gpu_key,
    cold_plate=cp_key,
    r1_die=r1_die,
    r4_manifold=r4_manifold,
    r5_cdu=r5_cdu,
    t_in=t_in,
    t_j_limit=t_j_limit,
    flow_starvation_pct=flow_starvation,
    cdu_drift_c=cdu_drift,
)
results = compute_thermal_chain(config)

# Also compute comparison with the other enabled cold plate
comparison_results = {}
for cp_k in enabled_plates:
    c = ThermalConfig(
        gpu=gpu_key, cold_plate=cp_k,
        r1_die=r1_die, r4_manifold=r4_manifold, r5_cdu=r5_cdu,
        t_in=t_in, t_j_limit=t_j_limit,
        flow_starvation_pct=flow_starvation, cdu_drift_c=cdu_drift,
    )
    comparison_results[cp_k] = compute_thermal_chain(c)

# --- Main Display ---

# Top metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    delta_color = "normal" if results.within_limit else "inverse"
    st.metric(
        "Junction Temperature",
        f"{results.t_j:.1f}°C",
        delta=f"{'within' if results.within_limit else 'EXCEEDS'} {results.t_j_limit:.0f}°C limit",
        delta_color=delta_color,
    )
with col2:
    st.metric("Total ΔT", f"{results.delta_t_total:.1f}°C")
with col3:
    st.metric("Chip Fraction", f"{results.chip_fraction:.0%}")
with col4:
    st.metric("R_total", f"{results.r_total:.4f} K/W")

if not results.within_limit:
    st.error(
        f"T_j = {results.t_j:.1f}°C **exceeds** the {results.t_j_limit:.0f}°C limit "
        f"by {results.t_j - results.t_j_limit:.1f}°C"
    )

st.divider()

# --- Resistance Chain Table ---
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("Thermal Resistance Chain")
    st.caption(f"T_j = T_in + Q × (R₁ + R₂₊₃ + R₄ + R₅)  |  Q = {results.q_tdp:.0f}W")

    chain_data = {
        "Layer": ["R₁", "R₂+R₃", "R₄", "R₅", "**Total**"],
        "Component": [
            "Silicon die bulk",
            COLD_PLATE_CONFIGS[cp_key]["label"],
            "Server manifold",
            "CDU heat exchanger",
            "",
        ],
        "R (K/W)": [
            f"{results.r1:.4f}",
            f"{results.r2_r3:.4f}",
            f"{results.r4:.4f}",
            f"{results.r5:.4f}",
            f"**{results.r_total:.4f}**",
        ],
        "ΔT (°C)": [
            f"{results.dt_die:.1f}",
            f"{results.dt_cold_plate:.1f}",
            f"{results.dt_manifold:.1f}",
            f"{results.dt_cdu:.1f}",
            f"**{results.delta_t_total:.1f}**",
        ],
    }
    st.dataframe(chain_data, use_container_width=True, hide_index=True)

with right_col:
    st.subheader("Resistance Breakdown")

    # Stacked bar chart of ΔT contributions
    fig = go.Figure()
    layers = ["R₁ Die", "R₂₊₃ Cold Plate", "R₄ Manifold", "R₅ CDU"]
    dts = [results.dt_die, results.dt_cold_plate, results.dt_manifold, results.dt_cdu]
    colors = ["#06b6d4", "#f59e0b", "#8b5cf6", "#64748b"]

    for layer, dt, color in zip(layers, dts, colors):
        fig.add_trace(go.Bar(
            name=layer, x=[dt], y=["ΔT"], orientation="h",
            marker_color=color,
            text=f"{dt:.1f}°C", textposition="inside",
        ))

    fig.update_layout(
        barmode="stack",
        plot_bgcolor="#111111", paper_bgcolor="#000000",
        font_color="white", height=150, margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True, legend=dict(orientation="h", y=-0.3),
        xaxis=dict(title="Temperature Rise (°C)", gridcolor="#333333"),
        yaxis=dict(visible=False),
    )
    # Add T_j limit line
    fig.add_vline(
        x=results.t_j_limit - results.t_in,
        line_dash="dash", line_color="#ef4444",
        annotation_text=f"T_j limit ({results.t_j_limit - results.t_in:.0f}°C headroom)",
        annotation_position="top",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Crossover Analysis ---
st.subheader("Crossover Analysis: Chip vs Rack")

cross_col1, cross_col2 = st.columns([1, 1])

with cross_col1:
    st.markdown("**Chip-level improvement vs JetCool baseline:**")
    if results.delta_t_saved_vs_baseline > 0:
        st.metric(
            "ΔT saved by selected cold plate",
            f"{results.delta_t_saved_vs_baseline:.1f}°C",
        )
    elif results.delta_t_saved_vs_baseline == 0:
        st.info("Selected cold plate IS the baseline (JetCool).")
    else:
        st.warning(
            f"Selected cold plate is {abs(results.delta_t_saved_vs_baseline):.1f}°C "
            "**worse** than JetCool baseline."
        )

    st.metric("Rack variation (CDU drift + flow)", f"{results.rack_variation:.1f}°C")

    if results.delta_t_saved_vs_baseline > 0 and results.rack_variation > 0:
        ratio = results.chip_wins_ratio
        if ratio > 1.5:
            st.success(f"**Chip wins by {ratio:.1f}×** — chip-level optimisation dominates")
        elif ratio > 0.8:
            st.warning(f"**Marginal ({ratio:.1f}×)** — both chip and rack matter")
        else:
            st.error(f"**Rack dominates ({ratio:.1f}×)** — rack-level co-design needed")

with cross_col2:
    st.markdown("**Crossover condition — chip wins when:**")
    st.code(
        f"ΔT_saved > δT_in + δT_flow\n"
        f"{results.delta_t_saved_vs_baseline:.1f}°C > {results.rack_variation:.1f}°C  "
        f"{'✓' if results.delta_t_saved_vs_baseline > results.rack_variation else '✗'}",
    )

    st.markdown("**Flow maldistribution penalty:**")
    st.code(
        f"At {flow_starvation:.0f}% starvation on {results.q_tdp:.0f}W node:\n"
        f"δT_j ≈ {results.dt_flow_starvation:.1f}°C uncompensated"
    )

st.divider()

# --- Cold Plate Comparison ---
st.subheader("Cold Plate Comparison")

comp_data = {
    "Cold Plate": [],
    "R₂₊₃ (K/W)": [],
    "T_j (°C)": [],
    "ΔT total (°C)": [],
    "Chip Fraction": [],
    "Within Limit": [],
}
for cp_k, cr in comparison_results.items():
    comp_data["Cold Plate"].append(COLD_PLATE_CONFIGS[cp_k]["label"])
    comp_data["R₂₊₃ (K/W)"].append(f"{cr.r2_r3:.4f}")
    comp_data["T_j (°C)"].append(f"{cr.t_j:.1f}")
    comp_data["ΔT total (°C)"].append(f"{cr.delta_t_total:.1f}")
    comp_data["Chip Fraction"].append(f"{cr.chip_fraction:.0%}")
    comp_data["Within Limit"].append("✓" if cr.within_limit else "✗")

st.dataframe(comp_data, use_container_width=True, hide_index=True)

# Comparison bar chart
fig2 = go.Figure()
for cp_k, cr in comparison_results.items():
    label = COLD_PLATE_CONFIGS[cp_k]["label"]
    fig2.add_trace(go.Bar(
        name=label,
        x=[label],
        y=[cr.t_j],
        text=f"{cr.t_j:.1f}°C",
        textposition="outside",
        marker_color="#06b6d4" if cr.within_limit else "#ef4444",
    ))

fig2.add_hline(
    y=results.t_j_limit,
    line_dash="dash", line_color="#ef4444",
    annotation_text=f"T_j limit = {results.t_j_limit:.0f}°C",
)
fig2.update_layout(
    plot_bgcolor="#111111", paper_bgcolor="#000000",
    font_color="white", height=350,
    yaxis=dict(title="Junction Temperature (°C)", gridcolor="#333333", range=[0, max(results.t_j_limit + 20, 120)]),
    showlegend=False,
    margin=dict(t=30),
)
st.plotly_chart(fig2, use_container_width=True)

# --- Quantitative Crossover Summary Table ---
st.divider()
st.subheader("Quantitative Crossover Summary")
st.caption("Dynamically computed from current parameters")

r_sicp = comparison_results.get("HP_SiCP")
r_jc = comparison_results.get("JetCool")

if r_sicp and r_jc:
    chip_gain = r_jc.t_j - r_sicp.t_j  # Temperature saved by SiCP vs JetCool
    rack_var = results.rack_variation
    stress_rack_var = 15.0 + results.dt_flow_starvation  # +15°C facility stress

    summary_data = {
        "Problem": [
            "Junction temp, nominal facility",
            "Junction temp, facility stress (+15°C T_in)",
            "Hydraulic flow maldistribution",
            "Service reliability topology",
        ],
        "Chip Gain": [
            f"{chip_gain:.1f}°C",
            f"{chip_gain:.1f}°C",
            "Cannot fix",
            "Cannot fix",
        ],
        "Rack Variation": [
            f"{rack_var:.1f}°C",
            f"~{stress_rack_var:.0f}°C",
            f"~{results.dt_flow_starvation:.1f}°C at {flow_starvation:.0f}% starvation",
            "Categorical",
        ],
        "Dominant Level": [
            f"{'Chip — wins by ' + f'{chip_gain/rack_var:.0f}×' if rack_var > 0 and chip_gain > rack_var else 'Marginal — both' if rack_var > 0 else 'Chip'}",
            f"{'Marginal — both' if abs(chip_gain - stress_rack_var) < 5 else ('Chip' if chip_gain > stress_rack_var else 'Rack')}",
            "Rack — different mechanism",
            "Rack — different variable space",
        ],
    }
    st.dataframe(summary_data, use_container_width=True, hide_index=True)

# --- Source Information ---
st.divider()
with st.expander("Sources & Methodology"):
    st.markdown("""
**Thermal resistance chain:** T_j = T_in + Q × (R₁ + R₂₊₃ + R₄ + R₅)

**Cold plate data sources:**
- HP SiCP: ARPA-E COOLERCHIPS target (0.010 K/W at 2 kW, <60 kPa). Cold plate only (R₂+R₃).
- JetCool SmartPlate: Published R_net = 0.021 K/W at H100 ~700W. Includes TIM.

**GPU TDP sources:**
- B100: 700W, B200 DGX: ~1000W, B200 full-spec: 1200W (NVIDIA published specs)

**Crossover methodology:** From West's problem-level localisation framework.
Chip wins when ΔT_saved > δT_in + δT_flow.

**Caution (Audit Note #2):** HP SiCP (0.010 K/W at 2 kW, 60 kPa) and JetCool
(0.021 K/W at ~700W) are measured at different heat flux and pressure conditions.
The comparison is indicative, not exact.

**Flow starvation model:** Linear scaling from reference point (4°C at 2000W, 30% starvation).
    """)
