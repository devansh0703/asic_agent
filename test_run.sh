#!/bin/bash
#
# Test script for ASIC-Agent
# Runs a simple counter design example
#

echo "======================================"
echo "ASIC-Agent Test - Simple Counter"
echo "======================================"
echo ""

# Check API key
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "ERROR: GOOGLE_API_KEY not set"
    echo "Get your free API key from: https://makersuite.google.com/app/apikey"
    echo "Then run: export GOOGLE_API_KEY='your-key-here'"
    exit 1
fi

echo "✓ API key found"
echo ""

# Clean workspace
echo "Cleaning workspace..."
rm -rf workspace chroma_db
mkdir -p workspace
echo "✓ Workspace ready"
echo ""

# Run ASIC-Agent
echo "Running ASIC-Agent..."
echo "Specification: Simple 4-bit counter"
echo ""

python3 main.py \
    --spec-file examples/simple_counter.txt \
    --name counter4 \
    --workspace ./workspace \
    --max-iterations 3 \
    --verbose

exit_code=$?

echo ""
echo "======================================"
if [ $exit_code -eq 0 ]; then
    echo "✓ TEST PASSED"
    echo ""
    echo "Generated files:"
    ls -lh workspace/
else
    echo "✗ TEST FAILED (exit code: $exit_code)"
fi
echo "======================================"

exit $exit_code
