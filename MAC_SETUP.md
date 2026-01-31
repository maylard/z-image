# Optimized Setup for Apple Silicon Mac (M4 Pro)

**Your Hardware:** MacBook Pro with Apple M4 Pro, 24GB RAM  
**GPU:** Metal Performance Shaders (MPS) - Apple's GPU acceleration

This guide provides the optimal configuration for your specific Mac.

---

## ✅ Current Optimal Settings

Your Mac is **already optimized** with these defaults in `createImage.py`:
- ✅ **Device:** MPS (Metal GPU acceleration) - auto-detected
- ✅ **Precision:** bfloat16 (best balance of speed/quality on Apple Silicon)
- ✅ **Compile:** False (torch.compile not optimal on MPS yet)

**You don't need to change anything!** Just run:
```bash
./createImage.sh
```

---

## 🚀 Performance Optimization Tips

### 1. **Use Native Flash Attention (Default)**
Your setup already uses `_native_flash` which works well on MPS.

```bash
# Already the default - no need to set
ZIMAGE_ATTENTION=_native_flash ./createImage.sh
```

### 2. **Optimal Image Sizes for 24GB RAM**

```bash
# ⚡ Fast (< 10 seconds) - RECOMMENDED for testing
ZIMAGE_HEIGHT=768 ZIMAGE_WIDTH=768 ./createImage.sh

# 🔥 Balanced (10-20 seconds) - DEFAULT, best quality/speed
ZIMAGE_HEIGHT=1024 ZIMAGE_WIDTH=1024 ./createImage.sh

# 💎 High Quality (20-40 seconds) - Still works great
ZIMAGE_HEIGHT=1536 ZIMAGE_WIDTH=1536 ./createImage.sh

# 🎨 Maximum (40-90 seconds) - You have the RAM for this!
ZIMAGE_HEIGHT=2048 ZIMAGE_WIDTH=2048 ./createImage.sh
```

**Your 24GB RAM means you can comfortably run 2048×2048 without issues!**

### 3. **Inference Steps Trade-off**

```bash
# Faster (4-6 steps) - slightly lower quality
ZIMAGE_STEPS=4 ./createImage.sh

# Default (8 steps) - RECOMMENDED balance
ZIMAGE_STEPS=8 ./createImage.sh

# Better quality (12-16 steps) - diminishing returns
ZIMAGE_STEPS=12 ./createImage.sh
```

### 4. **Batch Processing for Multiple Images**

If generating many images, use batch mode:
```bash
# Create prompts/prompt1.txt, prompts/prompt2.txt, etc.
mkdir -p prompts
echo "A sunset over mountains" > prompts/sunset.txt
echo "A futuristic city" > prompts/city.txt

# Generate all at once
python batch_inference.py
```

---

## ⚙️ Advanced: Fine-tune for Your Workflow

### For Speed (Quick Iterations)
```bash
ZIMAGE_HEIGHT=768 \
ZIMAGE_WIDTH=768 \
ZIMAGE_STEPS=6 \
./createImage.sh
```
**Expected time:** 5-8 seconds

### For Quality (Final Output)
```bash
ZIMAGE_HEIGHT=1536 \
ZIMAGE_WIDTH=1536 \
ZIMAGE_STEPS=12 \
./createImage.sh
```
**Expected time:** 25-35 seconds

### For Maximum Resolution
```bash
ZIMAGE_HEIGHT=2048 \
ZIMAGE_WIDTH=2048 \
ZIMAGE_STEPS=8 \
./createImage.sh
```
**Expected time:** 50-80 seconds

---

## 🔍 Benchmarking Your Setup

Run a quick test to see actual performance:

```bash
# Create test prompt
echo "A photorealistic mountain landscape at golden hour" > prompt.md

# Benchmark default (1024×1024)
time ./createImage.sh

# Benchmark high-res (1536×1536)
time ZIMAGE_HEIGHT=1536 ZIMAGE_WIDTH=1536 ./createImage.sh
```

**Expected Results on M4 Pro:**
- 1024×1024, 8 steps: ~12-18 seconds
- 1536×1536, 8 steps: ~25-35 seconds
- 2048×2048, 8 steps: ~50-70 seconds

---

## ⚠️ What NOT to Change

### ❌ Don't Enable torch.compile
```python
# In createImage.py, keep this as False
compile = False  # torch.compile not optimal on MPS
```

### ❌ Don't Force CPU
```bash
# Never do this - you'll lose 10x speed
# Your script auto-detects MPS correctly
```

### ❌ Don't Use float32
```python
# Keep this as bfloat16 in createImage.py
dtype = torch.bfloat16  # Optimal for Apple Silicon
```

### ❌ Don't Try Flash Attention 3
```bash
# _flash_3 is for NVIDIA Hopper GPUs (H100), won't work on Mac
# Stick with: _native_flash (default)
```

---

## 🎯 Recommended Workflow

### Daily Use (Fast Iterations)
```bash
# 768×768 for quick testing
ZIMAGE_HEIGHT=768 ZIMAGE_WIDTH=768 ./createImage.sh
```

### Final Outputs (High Quality)
```bash
# 1536×1536 for production
ZIMAGE_HEIGHT=1536 ZIMAGE_WIDTH=1536 ZIMAGE_STEPS=12 ./createImage.sh
```

### Print/Professional (Maximum)
```bash
# 2048×2048 for high-res needs
ZIMAGE_HEIGHT=2048 ZIMAGE_WIDTH=2048 ./createImage.sh
```

---

## 💾 Memory Usage Guide

Your **24GB Unified Memory** allocation (approximate):

| Image Size | Memory Used | Remaining | Status |
|------------|-------------|-----------|--------|
| 512×512    | ~3-4 GB     | ~20 GB    | ⚡ Very Fast |
| 768×768    | ~5-6 GB     | ~18 GB    | ⚡ Fast |
| 1024×1024  | ~7-9 GB     | ~15 GB    | ✅ Optimal |
| 1536×1536  | ~12-14 GB   | ~10 GB    | ✅ Great |
| 2048×2048  | ~18-20 GB   | ~4 GB     | ✅ Works |

**You have plenty of headroom!** Even 2048×2048 is comfortable.

---

## 🔧 Troubleshooting

### Script Running Slow?

1. **Check if MPS is active:**
   ```bash
   ./createImage.sh 2>&1 | grep "Chosen device"
   # Should see: "Chosen device: mps"
   ```

2. **Monitor memory:**
   ```bash
   # While script runs, open Activity Monitor
   # Look for "python" process memory usage
   ```

3. **Close heavy apps:**
   - Close Chrome/browser tabs
   - Close video editing software
   - Free up system memory

### Out of Memory (Rare with 24GB)?

```bash
# Reduce size
ZIMAGE_HEIGHT=1024 ZIMAGE_WIDTH=1024 ./createImage.sh

# Or use fewer steps
ZIMAGE_STEPS=6 ./createImage.sh
```

---

## 📊 Performance Comparison

**Your M4 Pro (MPS) vs Other Setups:**

| Hardware | 1024×1024 Time | Relative Speed |
|----------|----------------|----------------|
| **Your M4 Pro (MPS)** | **~15 sec** | **1.0× (baseline)** |
| M1/M2 Mac (MPS) | ~25-30 sec | 0.5-0.6× |
| CPU Only (M4) | ~120 sec | 0.12× |
| NVIDIA RTX 4090 | ~2-3 sec | 5-7× faster |
| NVIDIA H100 (compiled) | <1 sec | 15-20× faster |

**Your Mac is 8-10× faster than CPU-only, which is excellent for local development!**

---

## 🎨 Practical Examples for Your Setup

### Quick Draft (5-8 seconds)
```bash
echo "A cozy coffee shop interior, warm lighting" > prompt.md
ZIMAGE_HEIGHT=768 ZIMAGE_WIDTH=768 ZIMAGE_STEPS=6 ./createImage.sh
```

### Social Media Post (12-18 seconds)
```bash
echo "Product photography, minimalist background" > prompt.md
ZIMAGE_HEIGHT=1024 ZIMAGE_WIDTH=1024 ./createImage.sh
```

### Print Quality (25-35 seconds)
```bash
echo "Abstract art, vibrant colors, high detail" > prompt.md
ZIMAGE_HEIGHT=1536 ZIMAGE_WIDTH=1536 ZIMAGE_STEPS=12 ./createImage.sh
```

### Portfolio Piece (50-70 seconds)
```bash
echo "Epic fantasy landscape, cinematic lighting" > prompt.md
ZIMAGE_HEIGHT=2048 ZIMAGE_WIDTH=2048 ZIMAGE_STEPS=12 ./createImage.sh
```

---

## ✅ TL;DR - Your Optimal Setup

**You're already configured optimally!** Just use:

```bash
# Default (best balance)
./createImage.sh

# High quality when needed
ZIMAGE_HEIGHT=1536 ZIMAGE_WIDTH=1536 ./createImage.sh
```

**No changes needed to code.** Your M4 Pro + 24GB RAM handles Z-Image beautifully at default settings.

---

**Last Updated:** January 2026  
**Hardware:** Apple M4 Pro, 24GB RAM  
**PyTorch:** 2.9.1 with MPS support
