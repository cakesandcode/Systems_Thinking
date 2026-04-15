"""Thermal resistance chain model for chip-to-rack analysis.

Implements the series resistance equation:
    T_j = T_in + Q * (R1 + R2_R3 + R4 + R5)

where each R represents a layer in the thermal network from junction to ambient.
"""

from dataclasses import dataclass, field


# --- GPU Configurations ---

GPU_CONFIGS = {
    "B100": {"tdp_w": 700, "label": "NVIDIA B100 (700W)"},
    "B200_DGX": {"tdp_w": 1000, "label": "NVIDIA B200 DGX/HGX (1000W)"},
    "B200_FULL": {"tdp_w": 1200, "label": "NVIDIA B200 Full-Spec (1200W)"},
}

# --- Cold Plate Configurations ---
# R values are cold-plate-only (R2+R3), NOT full-stack R_net

COLD_PLATE_CONFIGS = {
    "HP_SiCP": {
        "r_cold_plate": 0.010,
        "label": "HP SiCP (Silicon Microchannel)",
        "technology": "MEMS silicon microchannel, metallic microbond to die",
        "source": "ARPA-E COOLERCHIPS target, 2 kW / 60 kPa",
        "enabled": True,
    },
    "JetCool": {
        "r_cold_plate": 0.021,
        "label": "JetCool SmartPlate (Copper)",
        "technology": "Microconvective jet impingement, copper",
        "source": "JetCool H100 datasheet, ~700W (R_net incl. TIM)",
        "enabled": True,
    },
    "Nexalus": {
        "r_cold_plate": 0.044,
        "label": "Nexalus SoloFlux (estimated)",
        "technology": "Jet impingement, single-slot",
        "source": "Estimated: R_net=0.052 K/W minus R1=0.008. RTX 4090 @ 415W, 4 L/min. NOT comparable conditions.",
        "enabled": False,  # Grayed out — data not comparable
    },
}

# --- Default Resistance Chain ---
# Values from chip_to_rack_thermal_framing.md

DEFAULT_R1_DIE = 0.008       # K/W — Silicon die bulk conduction
DEFAULT_R4_MANIFOLD = 0.005  # K/W — Server manifold fluid temperature rise
DEFAULT_R5_CDU = 0.0003      # K/W — CDU heat exchanger
DEFAULT_T_IN = 40.0          # °C — ASHRAE W4 inlet temperature
T_J_LIMIT = 90.0             # °C — NVIDIA junction temperature limit


@dataclass
class ThermalConfig:
    """Configuration for a thermal resistance chain calculation."""
    gpu: str = "B200_FULL"
    cold_plate: str = "HP_SiCP"
    r1_die: float = DEFAULT_R1_DIE
    r4_manifold: float = DEFAULT_R4_MANIFOLD
    r5_cdu: float = DEFAULT_R5_CDU
    t_in: float = DEFAULT_T_IN
    t_j_limit: float = T_J_LIMIT
    # Rack parameters
    flow_starvation_pct: float = 30.0
    cdu_drift_c: float = 3.0

    @property
    def q_tdp(self) -> float:
        return GPU_CONFIGS[self.gpu]["tdp_w"]

    @property
    def r_cold_plate(self) -> float:
        return COLD_PLATE_CONFIGS[self.cold_plate]["r_cold_plate"]


@dataclass
class ThermalResults:
    """Results from a thermal resistance chain calculation."""
    # Resistance chain
    r1: float = 0.0
    r2_r3: float = 0.0
    r4: float = 0.0
    r5: float = 0.0
    r_total: float = 0.0

    # Temperatures
    q_tdp: float = 0.0
    t_in: float = 0.0
    t_j: float = 0.0
    t_j_limit: float = T_J_LIMIT
    delta_t_total: float = 0.0

    # Per-layer deltas
    dt_die: float = 0.0
    dt_cold_plate: float = 0.0
    dt_manifold: float = 0.0
    dt_cdu: float = 0.0

    # Fractions
    chip_fraction: float = 0.0
    rack_fraction: float = 0.0

    # Crossover analysis
    delta_t_saved_vs_baseline: float = 0.0
    rack_variation: float = 0.0
    chip_wins_ratio: float = 0.0
    within_limit: bool = True

    # Flow maldistribution
    dt_flow_starvation: float = 0.0


def compute_thermal_chain(config: ThermalConfig) -> ThermalResults:
    """Compute the full thermal resistance chain and crossover analysis."""
    r = ThermalResults()

    # Resistance values
    r.r1 = config.r1_die
    r.r2_r3 = config.r_cold_plate
    r.r4 = config.r4_manifold
    r.r5 = config.r5_cdu
    r.r_total = r.r1 + r.r2_r3 + r.r4 + r.r5

    # TDP and inlet
    r.q_tdp = config.q_tdp
    r.t_in = config.t_in
    r.t_j_limit = config.t_j_limit

    # Per-layer temperature deltas: ΔT = Q × R
    r.dt_die = r.q_tdp * r.r1
    r.dt_cold_plate = r.q_tdp * r.r2_r3
    r.dt_manifold = r.q_tdp * r.r4
    r.dt_cdu = r.q_tdp * r.r5

    # Total
    r.delta_t_total = r.q_tdp * r.r_total
    r.t_j = r.t_in + r.delta_t_total
    r.within_limit = r.t_j <= r.t_j_limit

    # Chip vs rack fractions
    chip_r = r.r1 + r.r2_r3
    rack_r = r.r4 + r.r5
    if r.r_total > 0:
        r.chip_fraction = chip_r / r.r_total
        r.rack_fraction = rack_r / r.r_total

    # Crossover: chip improvement vs baseline (JetCool copper)
    r_baseline = COLD_PLATE_CONFIGS["JetCool"]["r_cold_plate"]
    r.delta_t_saved_vs_baseline = r.q_tdp * (r_baseline - r.r2_r3)

    # Rack variation: CDU drift + flow maldistribution
    r.rack_variation = config.cdu_drift_c + _flow_starvation_dt(
        r.q_tdp, config.flow_starvation_pct
    )

    # Chip wins ratio
    if r.rack_variation > 0:
        r.chip_wins_ratio = r.delta_t_saved_vs_baseline / r.rack_variation

    # Flow maldistribution penalty
    r.dt_flow_starvation = _flow_starvation_dt(
        r.q_tdp, config.flow_starvation_pct
    )

    return r


def _flow_starvation_dt(q_tdp: float, starvation_pct: float) -> float:
    """Approximate temperature penalty from flow starvation.

    From the framing doc: at 30% starvation on a 2 kW node, δT_j ≈ 4°C.
    Scale linearly with TDP and starvation percentage.
    """
    # Reference: 4°C at 2000W and 30% starvation
    if starvation_pct <= 0:
        return 0.0
    return 4.0 * (q_tdp / 2000.0) * (starvation_pct / 30.0)


def compute_comparison(configs: list[ThermalConfig]) -> list[ThermalResults]:
    """Compute thermal chains for multiple configurations for comparison."""
    return [compute_thermal_chain(c) for c in configs]
