# ADK Installation Troubleshooting

## Network Timeout Issues

If you encounter timeout errors when installing `google-adk`, try these solutions:

### Solution 1: Install with Increased Timeout

```bash
pip install --timeout=300 --retries=3 google-adk google-genai
```

### Solution 2: Install in Virtual Environment

Make sure you're in your virtual environment:

```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Then install
pip install google-adk google-genai
```

### Solution 3: Install Core Dependencies First

If the full installation fails, install core dependencies first:

```bash
# Step 1: Install google-genai (smaller package)
pip install google-genai

# Step 2: Install google-adk (will pull in remaining deps)
pip install google-adk
```

### Solution 4: Use Alternative Index

If PyPI is slow, try using a mirror:

```bash
pip install -i https://pypi.org/simple/ google-adk google-genai
```

### Solution 5: Install Without Optional Dependencies

For development, you can install minimal dependencies:

```bash
# Install only core ADK (without GCP dependencies)
pip install google-genai
pip install google-adk --no-deps
pip install pydantic fastapi uvicorn
```

### Solution 6: Check Network Connection

Verify your internet connection:

```bash
# Test connectivity
ping pypi.org
curl -I https://pypi.org/simple/
```

### Solution 7: Use pip Cache

If downloads keep failing, use pip's cache:

```bash
# Clear cache and retry
pip cache purge
pip install --no-cache-dir google-adk google-genai
```

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'google'"

**Cause**: Not installed or wrong Python environment

**Solution**:
```bash
# Verify you're in the right environment
which python
python --version  # Should be 3.11+

# Reinstall
pip install google-adk google-genai
```

### Issue: "Read timed out" during download

**Cause**: Network timeout downloading large packages

**Solution**:
```bash
# Increase timeout
pip install --timeout=600 google-adk google-genai

# Or install with retries
pip install --timeout=300 --retries=5 google-adk google-genai
```

### Issue: "Failed to establish connection"

**Cause**: Network connectivity issues

**Solution**:
1. Check your internet connection
2. Try again later
3. Use a VPN if behind a firewall
4. Check if you need proxy settings

## Verification

After installation, verify it works:

```python
# Test import
python -c "import google.adk; import google.genai; print('✅ ADK installed')"

# Or use our validation
python -c "from config.adk_config import validate_adk_setup; validate_adk_setup()"
```

## Alternative: Manual Installation

If pip continues to fail, you can:

1. Download wheels manually from PyPI
2. Install from local files:
   ```bash
   pip install /path/to/google-adk-*.whl
   pip install /path/to/google-genai-*.whl
   ```

## Getting Help

If installation continues to fail:

1. Check [ADK GitHub Issues](https://github.com/google/adk/issues)
2. Review [ADK Documentation](https://google.github.io/adk-docs/)
3. Check your Python version (requires 3.11+)
4. Ensure pip is up to date: `pip install --upgrade pip`

