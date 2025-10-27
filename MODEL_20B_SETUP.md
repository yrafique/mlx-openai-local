# Switching to GPT-OSS 20B Model

## ✅ What Was Done

Successfully configured the system to use the **20B parameter model** (`lmstudio-community/gpt-oss-20b-MLX-8bit`) instead of the default 3B model.

## 🔧 Changes Made

### 1. Updated `.env` Configuration
```bash
# Default Model (switching to 20B for better reasoning)
# Note: 20B model requires ~10-12GB RAM and is slower than 3B
DEFAULT_MODEL=lmstudio-community/gpt-oss-20b-MLX-8bit

# Alternative Models (comma-separated)
ALLOWED_MODELS=lmstudio-community/gpt-oss-20b-MLX-8bit,mlx-community/Qwen2.5-0.5B-Instruct-4bit,mlx-community/Qwen2.5-3B-Instruct-4bit,mlx-community/Qwen2.5-7B-Instruct-4bit,mlx-community/Llama-3.2-3B-Instruct-4bit
```

### 2. Model Downloaded
- **Size**: 12GB on disk (8-bit quantization)
- **Location**: `~/.cache/huggingface/hub/models--lmstudio-community--gpt-oss-20b-MLX-8bit`
- **Format**: MLX-optimized for Apple Silicon

## 📊 How It Works

### Important: Per-Request Model Loading

**MLX Omni Server** doesn't pre-load a default model. Instead:
1. ✅ Server starts without loading any model
2. ✅ When a request comes in with `"model": "lmstudio-community/gpt-oss-20b-MLX-8bit"`
3. ✅ Server loads that model into memory
4. ✅ Generates response
5. ✅ Model stays in memory for subsequent requests

**The UI uses the `DEFAULT_MODEL` from `.env`** when making API requests.

### How Each Component Works

```
┌─────────────────────────────────────────┐
│  User asks in UI                        │
│  "Is Apple buy or sell?"                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  UI (ControlPanel.py)                   │
│  Uses DEFAULT_MODEL from .env:          │
│  "lmstudio-community/gpt-oss-20b-MLX-8bit"│
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  API Request to MLX Omni Server         │
│  {                                       │
│    "model": "lmstudio-community/gpt-oss-20b-MLX-8bit",│
│    "messages": [...]                     │
│  }                                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  MLX Omni Server                        │
│  1. Receives request                    │
│  2. Sees model: gpt-oss-20b            │
│  3. Loads 20B model (first time: ~10-30s)│
│  4. Generates response                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Response                               │
│  Better reasoning with 20B model!       │
└─────────────────────────────────────────┘
```

## 🎯 Expected Behavior

### First Request (20B Model)
- **Load Time**: 10-30 seconds (model loads into memory)
- **Memory Usage**: ~10-12GB RAM
- **Response**: After loading, generates response

### Subsequent Requests
- **Load Time**: Instant (model already in memory)
- **Response Time**: 2-5 seconds (slower than 3B, but better quality)

## 🧪 How to Test

### Test in UI (http://localhost:7006)
1. Open http://localhost:7006
2. Clear chat
3. Enable "💰 Real-time Finance"
4. Ask: **"Is Apple buy or sell? Analyze the price movement."**

**Expected:**
- First time: Wait 10-30s for model to load
- Response: More detailed analysis than 3B model
- Includes reasoning about price trends, technical analysis, etc.

### Test via curl
```bash
# Request will use the model specified in the request
curl -X POST http://localhost:7007/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "lmstudio-community/gpt-oss-20b-MLX-8bit",
    "messages": [
      {"role": "user", "content": "Analyze if Apple stock is a buy or sell"}
    ],
    "max_tokens": 500
  }' | python3 -m json.tool
```

## 📋 Model Comparison

| Aspect | 3B Model | 20B Model |
|--------|----------|-----------|
| **Parameters** | 3 billion | 20 billion |
| **Memory** | ~4GB | ~10-12GB |
| **Load Time** | 2-5s | 10-30s |
| **Response Time** | <1s | 2-5s |
| **Quality** | Good | Excellent |
| **Reasoning** | Basic | Advanced |
| **Analysis Depth** | Surface | Deep |
| **Function Calling** | 99% (tested) | Unknown (not tested) |

## ⚠️ Important Notes

### 1. Function Calling Accuracy Unknown
- The 99% function calling accuracy is **only tested** on:
  - `mlx-community/Qwen2.5-3B-Instruct-4bit`
  - `mlx-community/Llama-3.2-3B-Instruct-4bit`
- The 20B model may have **different** function calling accuracy
- If tools don't work well, switch back to 3B models

### 2. Memory Requirements
- **Minimum**: 16GB RAM
- **Recommended**: 32GB RAM
- If you get out-of-memory errors, switch to Qwen2.5-7B or back to 3B

### 3. Performance
- **First query**: Very slow (10-30s) - model loading
- **Subsequent**: Moderate (2-5s per response)
- **Tip**: Keep server running, don't restart frequently

### 4. Answering "Buy or Sell?"
The 20B model should provide **better analysis** for investment questions:

**3B Model:**
```
AAPL is trading at $262.82 (+1.25%)
```

**20B Model (Expected):**
```
AAPL is trading at $262.82 (+1.25% from previous close).

Analysis:
- Short-term momentum is positive with +1.25% gain
- Price above previous close suggests buying pressure
- However, this is just one day's movement
- Consider broader factors: earnings, sector trends, market conditions

Recommendation: Neutral to slight buy for long-term investors.
Technical indicators suggest short-term strength, but always
consider your investment timeline and risk tolerance.
```

## 🔄 Switching Back to 3B

If the 20B model is too slow or doesn't work well:

1. **Edit `.env`:**
```bash
DEFAULT_MODEL=mlx-community/Llama-3.2-3B-Instruct-4bit
```

2. **Restart UI:**
```bash
./scripts/orchestrate.sh --stop-ui
./scripts/orchestrate.sh --start
```

3. **Done!** Next request will use 3B model

## 🎓 Understanding the Difference

### Why the original query didn't get "buy/sell" analysis:

**Query**: "Is Apple buy or sell?"

**What Happened:**
1. ✅ Financial tool fetched price: $262.82
2. ❌ But tool only returns **price data**, not **analysis**
3. ❌ Small 3B model didn't add interpretation

**With 20B Model:**
1. ✅ Financial tool fetches price
2. ✅ 20B model **analyzes** the data
3. ✅ Provides buy/sell **recommendation** with reasoning

The larger model has better reasoning capabilities to interpret the price data and provide actionable insights.

## 📝 Summary

- ✅ 20B model configured in `.env`
- ✅ Model downloaded (12GB)
- ✅ Server running and ready
- ✅ UI will use 20B model for all requests
- ⏱️ First request will take 10-30s (model loading)
- 🧠 Better reasoning for complex questions like "buy or sell?"

## 🚀 Next Steps

1. **Try it**: Ask "Is Apple buy or sell?" in the UI
2. **Compare**: Notice deeper analysis vs. just price data
3. **Adjust**: If too slow, switch to Qwen2.5-7B (middle ground)
4. **Monitor**: Watch memory usage with Activity Monitor

---

**Status**: ✅ Ready to use 20B model
**UI**: http://localhost:7006
**Expected**: Better analysis and reasoning for complex queries
