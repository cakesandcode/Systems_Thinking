# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Systems thinking analysis toolkit. Each analysis lives under `code/<analysis_name>/` with its own models, app, and tests. The Obsidian vault (`Systems_Thinker/`) provides research data as read-only input.

Current analyses:
- `code/chip_to_rack/` — Thermal resistance chain calculator for chip-to-rack framing

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the chip-to-rack Streamlit app
streamlit run code/chip_to_rack/app/app.py

# Run chip-to-rack tests
cd code/chip_to_rack && python -m pytest tests/ -v --tb=short
```

## Folder Structure

```
Systems_Thinking/
├── code/
│   └── chip_to_rack/           # Thermal framing analysis
│       ├── app/app.py          # Streamlit UI
│       ├── models/thermal.py   # Computation (no UI deps)
│       ├── tests/              # 22 tests
│       └── .streamlit/         # Dark theme
├── Systems_Thinker/            # Obsidian vault (read-only, not in git)
│   └── raw/
│       ├── Chip_to_rack/       # Original thermal framing analysis
│       ├── Cold_plates/        # HP SiCP, JetCool, Nexalus research
│       └── GPU_specifications/ # NVIDIA Blackwell TDPs
├── .claude/agents/             # 4 agent definitions
├── HOW_TO_SETUP.md
├── HOW_TO_RUN.md
└── ARCHITECTURE.md
```

## Key Design Decisions

- Code organized by analysis: `code/<name>/` — each self-contained with models, app, tests
- Computation separated from UI — models have no Streamlit imports
- Obsidian vault is read-only input, excluded from git
- Nexalus cold plate grayed out — R_net data not comparable

## Git Workflow

Feature branches merged to `main` via PR. Never commit directly to `main`.
