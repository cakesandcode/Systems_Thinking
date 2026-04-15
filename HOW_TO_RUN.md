# How To Run

## Start the App

All commands run from the **project root** (`Systems_Thinking/`), where the `.venv` lives:

```bash
cd /Users/arunakumar/Claude_Projects/Systems_Thinking
source .venv/bin/activate
streamlit run code/chip_to_rack/app/app.py
```

Opens in your browser at `http://localhost:8501`.

## Using the App

### Sidebar Inputs

**Configuration:**
- **GPU** — Select NVIDIA Blackwell GPU. Sets Q (TDP) in the thermal chain.
  - B100: 700W
  - B200 DGX/HGX: 1000W
  - B200 Full-Spec: 1200W
- **Cold Plate** — Select cold plate technology. Sets R₂+R₃ in the resistance chain.
  - HP SiCP (Silicon Microchannel): 0.010 K/W
  - JetCool SmartPlate (Copper): 0.021 K/W

**Thermal Parameters:**
- **Coolant Inlet T_in** — ASHRAE W4 default is 40°C. Range: 20-60°C.
- **Junction Limit T_j,max** — NVIDIA spec default is 90°C.

**Resistance Overrides:**
- **R₁ Die Bulk** — Silicon die conduction. Default: 0.008 K/W.
- **R₄ Manifold** — Server manifold fluid rise. Default: 0.005 K/W.
- **R₅ CDU** — CDU heat exchanger. Default: 0.0003 K/W.

**Rack Parameters:**
- **Flow Starvation %** — Hydraulic flow maldistribution. Default: 30%.
- **CDU Drift** — CDU inlet temperature variation. Default: 3°C.

### Main Display

1. **Top Metrics** — Junction temperature, total ΔT, chip fraction, R_total
2. **Resistance Chain Table** — Per-layer R values and ΔT contributions
3. **Resistance Breakdown Chart** — Stacked bar showing ΔT by layer with T_j limit line
4. **Crossover Analysis** — Chip gain vs rack variation, crossover condition evaluation
5. **Cold Plate Comparison** — Side-by-side T_j for all enabled cold plates
6. **Quantitative Summary Table** — Dynamic version of the crossover summary from the analysis

### Key Equation

```
T_j = T_in + Q × (R₁ + R₂₊₃ + R₄ + R₅)
```

Where Q is GPU TDP in watts and each R is thermal resistance in K/W.

## Run Tests

From the project root:

```bash
cd /Users/arunakumar/Claude_Projects/Systems_Thinking
source .venv/bin/activate
cd code/chip_to_rack
python -m pytest tests/ -v --tb=short
```

## Headless Mode

For remote servers without a browser:

```bash
streamlit run code/chip_to_rack/app/app.py --server.headless true --server.port 8501
```
