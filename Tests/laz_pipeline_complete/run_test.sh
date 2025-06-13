#!/bin/bash

# Complete LAZ Pipeline Test Runner
# This script runs the comprehensive LAZ processing pipeline test

echo "🧪 Complete LAZ Processing Pipeline Test"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "test_complete_laz_pipeline.py" ]; then
    echo "❌ Error: test_complete_laz_pipeline.py not found"
    echo "Please run this script from the Tests/laz_pipeline_complete directory"
    exit 1
fi

# Check if FoxIsland.laz exists
LAZ_FILE="../../input/LAZ/FoxIsland.laz"
if [ ! -f "$LAZ_FILE" ]; then
    echo "❌ Error: FoxIsland.laz not found at $LAZ_FILE"
    echo "Please ensure the LAZ file exists in input/LAZ/"
    exit 1
fi

# Get LAZ file size for estimation
LAZ_SIZE=$(stat -f%z "$LAZ_FILE" 2>/dev/null || stat -c%s "$LAZ_FILE" 2>/dev/null)
LAZ_SIZE_MB=$((LAZ_SIZE / 1024 / 1024))

echo "📄 Input file: FoxIsland.laz (${LAZ_SIZE_MB} MB)"
echo "📁 Output directory: outputs/"
echo ""

# Estimate runtime based on file size
if [ $LAZ_SIZE_MB -lt 50 ]; then
    echo "⏱️ Estimated runtime: 2-5 minutes"
elif [ $LAZ_SIZE_MB -lt 200 ]; then
    echo "⏱️ Estimated runtime: 5-15 minutes"
else
    echo "⏱️ Estimated runtime: 15+ minutes"
fi

echo ""
echo "🚀 Starting complete LAZ processing pipeline test..."
echo ""

# Run the test
python test_complete_laz_pipeline.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Test completed successfully!"
    echo ""
    echo "📁 Generated files in outputs/:"
    if [ -d "outputs" ]; then
        ls -la outputs/ | grep -E '\.(tif|png)$' | while read line; do
            echo "   $line"
        done
    fi
    echo ""
    echo "🖼️ View PNG files to see the visualization results"
else
    echo ""
    echo "❌ Test failed!"
    echo "Check the error messages above for troubleshooting"
    exit 1
fi
