# How To Setup

## Prerequisites

- Python 3.12+
- macOS (tested on Apple Silicon)

## Steps

1. Clone the repository:

```bash
git clone <repo-url>
cd Systems_Thinking
```

2. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` — interactive web UI
- `plotly` — charts and visualizations
- `pytest` — test framework

4. (Optional) Set up the Obsidian vault:

The app reads research data from `Systems_Thinker/raw/` but does not require it to run. If you want the research notes:
- Create a `Systems_Thinker/` directory in the project root
- Add your Obsidian vault with `.md` research files under `raw/`

The vault is excluded from git via `.gitignore`.

## Verify Installation

```bash
cd code/chip_to_rack
python -m pytest tests/ -v --tb=short
```

All 22 tests should pass.
