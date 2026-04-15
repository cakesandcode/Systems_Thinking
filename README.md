# Systems Thinking — Chip-to-Rack Thermal Framing

Interactive parametric calculator for chip-to-rack thermal framing analysis. Compares cold plate technologies across NVIDIA Blackwell GPU configurations using Geoffrey West's problem-level localisation framework.

![App Screenshot](https://github.com/cakesandcode/Systems_Thinking/raw/main/docs/app_screenshot.png)

## The Problem

The chip-vs-rack thermal debate is framed as a binary: either the chip controls its own thermal destiny, or it requires rack-level co-design. Both positions are wrong — different problems are localised at different levels of the thermal network hierarchy.

This tool lets you explore that quantitatively.

## What It Does

- **Thermal resistance chain:** Computes T_j = T_in + Q × (R₁ + R₂₊₃ + R₄ + R₅) with configurable parameters
- **Cold plate comparison:** HP SiCP (Silicon Microchannel) vs JetCool SmartPlate (Copper) side-by-side
- **GPU configurations:** NVIDIA B100 (700W), B200 DGX (1000W), B200 Full-Spec (1200W)
- **Crossover analysis:** Chip gain vs rack variation — determines which level dominates
- **Quantitative summary:** Dynamic crossover table showing dominant level for each thermal problem

## Quick Start

```bash
git clone https://github.com/cakesandcode/Systems_Thinking.git
cd Systems_Thinking
./setup.sh
source .venv/bin/activate
streamlit run code/chip_to_rack/app/app.py
```

Opens at `http://localhost:8501`.

## Project Structure

```
Systems_Thinking/
├── code/
│   └── chip_to_rack/
│       ├── app/app.py              # Streamlit UI
│       ├── models/thermal.py       # Computation engine (no UI deps)
│       └── tests/test_thermal.py   # 22 tests
├── setup.sh                        # One-command setup
├── ARCHITECTURE.md                 # Design decisions and data flow
├── HOW_TO_SETUP.md                 # Setup instructions
└── HOW_TO_RUN.md                   # Usage guide
```

## The Thermal Resistance Chain

```
T_j = T_in + Q × (R₁ + R₂₊₃ + R₄ + R₅)
```

| Layer | Component | Default R (K/W) |
|---|---|---|
| R₁ | Silicon die bulk conduction | 0.008 |
| R₂+R₃ | Cold plate (HP SiCP / JetCool) | 0.010 / 0.021 |
| R₄ | Server manifold fluid rise | 0.005 |
| R₅ | CDU heat exchanger | 0.0003 |

At 1200W GPU TDP and 40°C inlet, HP SiCP delivers a 22°C junction temperature improvement over the JetCool copper baseline. Rack-level variation totals ~7°C. Chip wins by 3×.

## Key Finding

Each thermal problem has a natural level where it is localised:

| Problem | Dominant Level |
|---|---|
| Junction temperature | **Chip** — wins by 3× |
| MZM photonic stability | **Decoupled** — non-constraint |
| MRM heater compensation | **PIC control loop** |
| Hydraulic flow imbalance | **Rack** |
| Service reliability | **Rack** |

Solving a problem at the wrong level is wasted engineering.

## Sources

- HP Inc. ARPA-E COOLERCHIPS presentations (Oct 2023, Dec 2024)
- JetCool H100 SmartPlate datasheet
- NVIDIA DGX B200 / GB200 NVL72 documentation
- West, G. *Scale: The Universal Laws of Growth, Innovation, Sustainability, and the Pace of Life*. Penguin Press, 2017.

## Tests

```bash
cd code/chip_to_rack
python -m pytest tests/ -v --tb=short
```

22 tests covering resistance chain, junction limits, crossover conditions, flow starvation, and configuration validation.

## License

MIT

## Author

Aruna Kumar — [armfirmware.substack.com](https://armfirmware.substack.com)
