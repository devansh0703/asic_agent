#!/bin/bash
# Setup script for ASIC-Agent knowledge base

echo "=========================================="
echo "ASIC-Agent Knowledge Base Setup"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Install additional dependencies for scraping
echo ""
echo "Installing web scraping dependencies..."
pip install beautifulsoup4 requests lxml || {
    echo "Error: Failed to install dependencies"
    exit 1
}

echo "✓ Dependencies installed"

# Build knowledge base
echo ""
echo "Building knowledge base from real documentation..."
echo "This will:"
echo "  - Scrape cocotb docs from docs.cocotb.org"
echo "  - Fetch cocotb examples from GitHub"
echo "  - Scrape OpenLane documentation"
echo "  - Add curated Verilog patterns"
echo ""

python3 scripts/build_knowledge_base.py || {
    echo "Error: Failed to build knowledge base"
    exit 1
}

echo ""
echo "=========================================="
echo "✓ Knowledge base setup complete!"
echo "=========================================="
echo ""
echo "You can now run ASIC-Agent with full documentation:"
echo "  python3 main.py \"Design a counter\" --name counter"
echo ""
