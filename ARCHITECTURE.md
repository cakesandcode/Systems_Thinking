# Architecture

## Overview

Interactive parametric calculator for chip-to-rack thermal framing analysis. Implements the series thermal resistance chain from GPU junction to ambient, comparing cold plate technologies across NVIDIA Blackwell GPU configurations.

Based on Geoffrey West's problem-level localisation framework: each problem in the thermal network hierarchy has a natural level at which it is localised, determined by the physics.

## Data Flow

```
Sidebar Inputs (GPU, cold plate, T_in, R overrides, rack params)
    ↓
ThermalConfig dataclass (single source of truth)
    ↓
compute_thermal_chain() — pure function, no side effects
    ↓
ThermalResults dataclass (all computed values)
    ↓
Streamlit UI (metrics, tables, Plotly charts)
```

## Module Structure

```
Systems_Thinking/
├── code/
│   └── chip_to_rack/               # Thermal framing analysis
│       ├── app/
│       │   └── app.py              # Streamlit UI — reads from models/
│       ├── models/
│       │   └── thermal.py          # Core computation — no UI dependencies
│       ├── tests/
│       │   └── test_thermal.py     # 22 tests
│       └── .streamlit/
│           └── config.toml         # Dark theme
├── .claude/
│   └── agents/                     # 4 agent definitions
├── Systems_Thinker/                # Obsidian vault (read-only, not in git)
│   └── raw/
│       ├── Chip_to_rack/           # Original thermal framing analysis
│       ├── Cold_plates/            # HP SiCP, JetCool, Nexalus research
│       └── GPU_specifications/     # NVIDIA Blackwell TDPs
├── HOW_TO_SETUP.md
├── HOW_TO_RUN.md
└── ARCHITECTURE.md
```

Each analysis under `code/` is self-contained: own models, app, tests. Adding a new analysis means creating `code/<new_analysis>/` with the same structure.

## Import DAG (within code/chip_to_rack/)

```
models/thermal.py    ← no project imports (stdlib only)
    ↑
app/app.py           ← models.thermal
    ↑
tests/test_thermal.py ← models.thermal
```

No circular dependencies. `models/thermal.py` is independently testable with no UI or framework dependency.

## Core Model: Thermal Resistance Chain

### Equation

```
T_j = T_in + Q × (R₁ + R₂₊₃ + R₄ + R₅)
```

### Resistance Layers

| Layer | Component | Default R (K/W) | Source |
|---|---|---|---|
| R₁ | Silicon die bulk conduction | 0.008 | chip_to_rack_thermal_framing.md |
| R₂+R₃ | Cold plate (configurable) | 0.010 (SiCP) / 0.021 (JetCool) | ARPA-E / JetCool datasheet |
| R₄ | Server manifold fluid rise | 0.005 | chip_to_rack_thermal_framing.md |
| R₅ | CDU heat exchanger | 0.0003 | chip_to_rack_thermal_framing.md |

### GPU Configurations

| GPU | TDP (W) | Source |
|---|---|---|
| B100 | 700 | NVIDIA published spec |
| B200 DGX/HGX | 1000 | NVIDIA DGX B200 datasheet |
| B200 Full-Spec | 1200 | TweakTown / TechPowerUp |

### Cold Plate Configurations

| Cold Plate | R₂₊₃ (K/W) | Status | Notes |
|---|---|---|---|
| HP SiCP | 0.010 | Enabled | ARPA-E COOLERCHIPS target, 2 kW / <60 kPa |
| JetCool SmartPlate | 0.021 | Enabled | H100 measured R_net (incl. TIM), ~700W |
| Nexalus SoloFlux | 0.044 | Disabled | R_net=0.052 full-stack, not comparable |

### Crossover Analysis

**Chip-level improvement:**
```
ΔT_saved = Q × (R_baseline - R_selected)
```
Where R_baseline = JetCool (0.021 K/W).

**Rack-level variation:**
```
rack_variation = CDU_drift + flow_starvation_ΔT
```

**Crossover condition — chip wins when:**
```
ΔT_saved > rack_variation
```

### Flow Starvation Model

Linear scaling from reference point:
```
δT = 4°C × (Q / 2000W) × (starvation% / 30%)
```
Reference: 4°C at 2 kW, 30% starvation (from Hagen-Poiseuille analysis in framing doc).

## Design Decisions

1. **Computation separated from UI** — `models/thermal.py` has no Streamlit imports; testable in isolation
2. **ThermalConfig as single source of truth** — all parameters flow through one dataclass
3. **Pure function computation** — `compute_thermal_chain()` takes config, returns results, no side effects
4. **Nexalus disabled** — R_net data (full die-to-coolant stack) not comparable to cold-plate-only R values from HP SiCP and JetCool; different TDP and pressure conditions
5. **Dark theme** — consistent with Financial_Modeling and ARM_SW_Stack projects
6. **Obsidian vault read-only** — research data stays in the vault, code never modifies it

## Agent Pipeline

```
software-architect → code-writer → code-reviewer
```

- **software-architect** — designs module interfaces, read-only tools
- **code-writer** — implements specs, full edit tools
- **code-reviewer** — Karpathy-style review, read-only tools
- **ui-architect** — Streamlit layout and chart design
