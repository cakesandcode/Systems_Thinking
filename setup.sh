#!/bin/bash
# Setup script for Systems_Thinking project

set -e

echo "Setting up Systems_Thinking..."

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Suppress Streamlit welcome prompt and telemetry
mkdir -p ~/.streamlit
cat > ~/.streamlit/credentials.toml << 'EOF'
[general]
email = ""
EOF
cat > ~/.streamlit/config.toml << 'EOF'
[browser]
gatherUsageStats = false
EOF

echo ""
echo "Setup complete. To run:"
echo "  source .venv/bin/activate"
echo "  streamlit run code/chip_to_rack/app/app.py"
