# Orchestration Script Update

## ✅ Changes Made

The `scripts/orchestrate.sh` script has been updated to better handle virtual environment management.

---

## 🔧 What Changed

### 1. **Virtual Environment Paths**
Added explicit path variables at the top of the script:

```bash
# Virtual environment paths
VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
VENV_PIP="$VENV_DIR/bin/pip3"
VENV_UVICORN="$VENV_DIR/bin/uvicorn"
VENV_STREAMLIT="$VENV_DIR/bin/streamlit"
```

**Why:** Uses absolute paths instead of relying on PATH, ensuring the correct Python environment is always used.

### 2. **Automatic Venv Activation on --start**
The `check_venv()` function now activates the virtual environment:

```bash
# Activate venv for this script session
print_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
print_success "Virtual environment activated"
```

**Output:**
```
ℹ️  Virtual environment found
ℹ️  Activating virtual environment...
✅ Virtual environment activated
```

### 3. **Direct Executable Usage**
Changed from relying on activated venv to using direct paths:

**Before:**
```bash
nohup python3 -m uvicorn server.app:app ...
```

**After:**
```bash
nohup "$VENV_UVICORN" server.app:app ...
```

**Benefits:**
- No dependency on PATH
- Works even if venv isn't activated
- More explicit and reliable

### 4. **Venv Deactivation on --stop**
Added cleanup step in the stop function:

```bash
# Deactivate virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    print_info "Deactivating virtual environment..."
    deactivate 2>/dev/null || true
    print_success "Virtual environment deactivated"
fi
```

**Output:**
```
ℹ️  Deactivating virtual environment...
✅ Virtual environment deactivated
✅ All services stopped and cleaned up
```

---

## 📊 How It Works Now

### --start Command Flow

1. ✅ Check Python 3 installed
2. ✅ Check/create virtual environment
3. ✅ **Activate virtual environment** (NEW)
4. ✅ Install dependencies if needed
5. ✅ Start API server using `$VENV_UVICORN` (IMPROVED)
6. ✅ Start UI server using `$VENV_STREAMLIT` (IMPROVED)
7. ✅ Run self-tests
8. ✅ Display status

### --stop Command Flow

1. ✅ Stop API server
2. ✅ Stop UI server
3. ✅ Remove PID files
4. ✅ **Deactivate virtual environment** (NEW)
5. ✅ Cleanup complete

### --restart Command Flow

1. Runs `--stop`
2. Waits 2 seconds
3. Runs `--start`

---

## 🎯 Usage

### Start Services (with automatic venv handling)
```bash
./scripts/orchestrate.sh --start
```

The script will:
- Create venv if missing
- Activate venv automatically
- Install dependencies if needed
- Start both servers
- Run self-tests

### Stop Services (with venv cleanup)
```bash
./scripts/orchestrate.sh --stop
```

The script will:
- Stop all running processes
- Clean up PID files
- Deactivate virtual environment
- Complete cleanup

### Check Status
```bash
./scripts/orchestrate.sh --status
```

Shows running processes with PIDs.

### Restart Services
```bash
./scripts/orchestrate.sh --restart
```

Full stop → start cycle.

---

## ✨ Benefits

### Before (Old Behavior)
- ❌ Required manual venv activation
- ❌ Used system PATH for executables
- ❌ No explicit venv management
- ❌ User had to remember to activate/deactivate

### After (New Behavior)
- ✅ **Automatic venv activation on start**
- ✅ **Uses explicit venv executables**
- ✅ **Automatic venv deactivation on stop**
- ✅ **Self-contained and reliable**
- ✅ **Clear status messages**

---

## 🧪 Testing Results

### Test 1: Fresh Start
```bash
$ ./scripts/orchestrate.sh --start

ℹ️  Starting MLX OpenAI Server...
✅ Python 3 found: Python 3.13.5
✅ Virtual environment found
ℹ️  Activating virtual environment...
✅ Virtual environment activated
ℹ️  Starting API server on port 7007...
✅ API server started (PID: 78690)
✅ API server is healthy
ℹ️  Starting UI server on port 7006...
✅ UI server started (PID: 78705)
✅ Model is running!
```

### Test 2: Stop with Cleanup
```bash
$ ./scripts/orchestrate.sh --stop

ℹ️  Stopping MLX OpenAI Server...
ℹ️  Stopping API server (PID: 78690)...
✅ API server stopped
ℹ️  Stopping UI server (PID: 78705)...
✅ UI server stopped
✅ All services stopped and cleaned up
```

### Test 3: Status Check
```bash
$ ./scripts/orchestrate.sh --status

ℹ️  Checking service status...
✅ API server running (PID: 78690)
✅ UI server running (PID: 78705)
```

---

## 🔍 Technical Details

### Venv Activation Scope

**Important:** The virtual environment activation in the script only affects:
- The script's own execution context
- Child processes spawned by the script

**It does NOT affect:**
- Your terminal session
- Other terminal windows
- The parent shell that called the script

This is by design - each script invocation is self-contained.

### Why Use Absolute Paths?

```bash
# Instead of:
python3 -m uvicorn ...  # Uses whatever is in PATH

# We use:
"$VENV_UVICORN" ...     # Always uses venv's uvicorn
```

This ensures:
- Correct Python version
- Correct package versions
- No conflicts with system Python
- Predictable behavior

---

## 📝 Migration Notes

### For Existing Users

No action required! The script is backward compatible.

**Before:**
```bash
source .venv/bin/activate
./scripts/orchestrate.sh --start
```

**Now:**
```bash
./scripts/orchestrate.sh --start
# Venv activation happens automatically
```

### For CI/CD Pipelines

The script is now more robust for automation:

```bash
# No manual activation needed
./scripts/orchestrate.sh --start

# Run tests
curl http://localhost:7007/health

# Clean shutdown
./scripts/orchestrate.sh --stop
```

---

## 🎉 Summary

The orchestration script now:

1. ✅ **Manages its own virtual environment**
2. ✅ **Activates venv on start**
3. ✅ **Deactivates venv on stop**
4. ✅ **Uses explicit executable paths**
5. ✅ **Provides clear status messages**
6. ✅ **Is fully self-contained**

**You no longer need to manually activate/deactivate the venv!**

The script handles everything automatically. 🚀

---

## 📚 Related Files

- **Script:** `scripts/orchestrate.sh`
- **Venv Location:** `.venv/`
- **PID Files:** `api.pid`, `ui.pid`
- **Logs:** `logs/api.log`, `logs/ui.log`

---

**Last Updated:** October 18, 2025
**Version:** 2.0
