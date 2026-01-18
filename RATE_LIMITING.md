# Rate Limiting Configuration

## Overview
Rate limiting prevents hitting API quota limits by adding delays between requests.

## Default Settings (Gemini Free Tier Safe)
- **Provider**: OpenRouter (Gemini)
- **Rate Limit**: 6.0 seconds between requests
- **Max Requests**: ~10 per minute (safe for Gemini's 15/min limit)
- **Status**: Enabled by default

## Gemini API Limits
- **Free Tier**: 15 requests/minute, 1,500 requests/day
- **Rate Limit Math**: 60 seconds ÷ delay = requests/min
  - 6.0s delay = 10 req/min ✅ Safe
  - 4.0s delay = 15 req/min ⚠️ At limit
  - 3.0s delay = 20 req/min ❌ Will fail

## Usage

### Use Gemini with Safe Rate Limiting (Recommended)
```bash
export OPENROUTER_API_KEY="your_key_here"
python3 main.py "Design spec" --name my_design
```
Default: 6s delay (10 req/min)

### Custom Rate Limit
```bash
# Faster (15 req/min - at limit)
python3 main.py "Design spec" --name my_design --rate-limit 4.0

# Safer (12 req/min)
python3 main.py "Design spec" --name my_design --rate-limit 5.0

# Very conservative (6 req/min)
python3 main.py "Design spec" --name my_design --rate-limit 10.0
```

### Disable Rate Limiting (Paid Tier Only)
```bash
python3 main.py "Design spec" --name my_design --no-rate-limit
```

### Use Mistral Instead
```bash
export MISTRAL_API_KEY="your_mistral_key"
python3 main.py "Design spec" --name my_design --provider mistral
```

## Configuration File
Edit `asic_agent/config.py`:
```python
rate_limit_enabled: bool = True
rate_limit_delay_seconds: float = 6.0
rate_limit_requests_per_minute: int = 10
```

## How It Works
1. Before each API call, check time since last request
2. If less than `rate_limit_delay`, sleep for remaining time
3. Log rate limiting delays in debug mode
4. Tracks per-client instance (orchestrator level)

## Typical Workflow Request Counts
- **Simple Design (counter)**:
  - RTL Generation: 1 request
  - Verification: 2-4 requests (testbench + debug iterations)
  - Total: ~3-5 requests (~18-30 seconds with 6s delay)

- **Complex Design**:
  - RTL Generation: 2-3 requests
  - Verification: 5-10 requests
  - Hardening: 3-5 requests
  - Total: ~10-18 requests (~60-108 seconds with 6s delay)

## Troubleshooting

### "Rate limit exceeded" errors
Increase delay:
```bash
--rate-limit 8.0  # More conservative
```

### Workflow too slow
Decrease delay (if on paid tier):
```bash
--rate-limit 2.0  # Faster, but risky on free tier
```

### Check current settings
Look for log line:
```
Rate limiting enabled: 6.0s delay between requests (10.0 req/min)
```

## Best Practices
1. ✅ Use default 6s delay for Gemini free tier
2. ✅ Enable rate limiting always (unless paid tier)
3. ✅ Monitor logs for rate limit errors
4. ⚠️ Don't go below 4s delay on free tier
5. ❌ Never disable rate limiting on free tier
