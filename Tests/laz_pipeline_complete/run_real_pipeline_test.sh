#!/bin/bash

# Real Pipeline Test Runner
# This script runs the actual process_all_raster_products() pipeline on FoxIsland.laz

echo "🧪 Real LAZ Pipeline Test - process_all_raster_products()"
echo "=========================================================="

# Check if we're in the right directory
if [ ! -f "test_real_pipeline.py" ]; then
    echo "❌ Error: test_real_pipeline.py not found"
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
echo "🎯 Testing: process_all_raster_products() function"
echo "📁 Output: output/FoxIsland/lidar/"
echo ""

# Estimate runtime
if [ $LAZ_SIZE_MB -lt 50 ]; then
    echo "⏱️ Estimated runtime: 3-8 minutes"
elif [ $LAZ_SIZE_MB -lt 200 ]; then
    echo "⏱️ Estimated runtime: 8-20 minutes"
else
    echo "⏱️ Estimated runtime: 20+ minutes"
fi

echo ""
echo "🔄 Expected outputs:"
echo "   • DTM generation from LAZ"
echo "   • 3 hillshades (315°, 45°, 135°) for RGB channels"
echo "   • RGB composite creation"
echo "   • Color relief generation"
echo "   • Tint overlay (color relief + RGB)"
echo "   • Slope relief analysis"
echo "   • Final blend (tint + slope)"
echo "   • PNG conversions for visualization"
echo ""

echo "🚀 Starting real pipeline test..."
echo ""

# Run the test
python test_real_pipeline.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Real pipeline test completed successfully!"
    echo ""
    echo "📁 Check generated files in:"
    if [ -d "../../output/FoxIsland/lidar" ]; then
        echo "   output/FoxIsland/lidar/"
        
        # Show directory structure
        echo ""
        echo "📂 Generated directory structure:"
        find ../../output/FoxIsland/lidar -type f -name "*.tif" -o -name "*.png" | head -20 | while read file; do
            rel_path=$(echo $file | sed 's|../../output/FoxIsland/lidar/||')
            size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
            size_mb=$((size / 1024 / 1024))
            echo "   📄 $rel_path (${size_mb} MB)"
        done
        
        total_files=$(find ../../output/FoxIsland/lidar -type f -name "*.tif" -o -name "*.png" | wc -l)
        echo "   ... and $total_files total files"
    fi
    echo ""
    echo "🎉 Workflow validation: 3-hillshade RGB → tint → slope blend confirmed!"
else
    echo ""
    echo "❌ Real pipeline test failed!"
    echo "Check the error messages above for troubleshooting"
    exit 1
fi
