#!/usr/bin/env bash
# Quick benchmark for your Mac setup

echo "=== Z-Image Mac Performance Benchmark ==="
echo "Hardware: $(sysctl -n machdep.cpu.brand_string 2>/dev/null || system_profiler SPHardwareDataType | grep Chip)"
echo "Memory: $(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB"}')"
echo ""

# Create test prompt if needed
if [ ! -f prompt.md ]; then
  echo "A serene mountain landscape at sunset, golden hour lighting" > prompt.md
fi

echo "Running benchmarks..."
echo ""

echo "Test 1: 768×768 (Quick)"
time ZIMAGE_HEIGHT=768 ZIMAGE_WIDTH=768 ZIMAGE_OUTPUT=test_768.png ./createImage.sh 2>&1 | grep -E "(Chosen|Time taken)"
echo ""

echo "Test 2: 1024×1024 (Default)"  
time ZIMAGE_HEIGHT=1024 ZIMAGE_WIDTH=1024 ZIMAGE_OUTPUT=test_1024.png ./createImage.sh 2>&1 | grep -E "(Chosen|Time taken)"
echo ""

echo "Test 3: 1536×1536 (High Quality)"
time ZIMAGE_HEIGHT=1536 ZIMAGE_WIDTH=1536 ZIMAGE_OUTPUT=test_1536.png ./createImage.sh 2>&1 | grep -E "(Chosen|Time taken)"
echo ""

echo "=== Benchmark Complete ==="
echo "Test images: test_768.png, test_1024.png, test_1536.png"
