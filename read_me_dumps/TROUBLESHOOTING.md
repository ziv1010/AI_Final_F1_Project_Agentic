# Troubleshooting Guide - F1 Analysis Agent Web Interface

## Issue: "Analyze" Button Not Working

### Symptoms
- Clicking the "Analyze" button does nothing
- No progress monitor appears
- Browser console shows network errors
- Connection status shows "Backend Disconnected"

### Root Cause
**The backend server is not running!**

The frontend is just a user interface that needs to communicate with the backend Python server. When you click "Analyze", the frontend tries to send a request to `http://localhost:5000/api/analyze`, but if the backend isn't running, the request fails silently.

### Solution: Start the Backend

#### Option 1: Development Mode (Recommended)

**Terminal 1 - Backend:**
```bash
cd /Users/ziv/Desktop/AI_Final_Project_F1/AI_Final_F1_Project_Agentic
source f1env_new/bin/activate
python backend/app.py
```

You should see:
```
Starting F1 Analysis Agent Backend...
Backend API: http://localhost:5000
WebSocket: ws://localhost:5000
 * Running on http://127.0.0.1:5000
```

**Terminal 2 - Frontend:**
```bash
cd /Users/ziv/Desktop/AI_Final_Project_F1/AI_Final_F1_Project_Agentic/frontend
npm start
```

You should see:
```
Compiled successfully!
Local: http://localhost:3000
```

Now:
1. Open http://localhost:3000
2. Check the connection status in the top-right (should show "Backend Connected")
3. Try clicking "Analyze" again

#### Option 2: Production Mode

```bash
cd /Users/ziv/Desktop/AI_Final_Project_F1/AI_Final_F1_Project_Agentic
./start_web.sh
```

Then open http://localhost:5000

### Verification

**Check if backend is running:**
```bash
./check_backend.sh
```

Should show:
```
✅ Backend is running and healthy!
```

**Or manually:**
```bash
curl http://localhost:5000/api/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-08T..."
}
```

## Common Issues

### 1. "Module not found" errors when starting backend

**Problem:**
```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**
```bash
pip install -r requirements-web.txt
```

### 2. Port 5000 already in use

**Problem:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**

**Option A:** Kill the process using port 5000
```bash
lsof -ti:5000 | xargs kill -9
```

**Option B:** Change the port in `backend/app.py` (line 310):
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5001)  # Changed to 5001
```

Then also update `frontend/package.json`:
```json
{
  "proxy": "http://localhost:5001"
}
```

### 3. Frontend won't compile

**Problem:**
```
Error: Cannot find module 'react'
```

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### 4. CORS errors in browser console

**Problem:**
```
Access to fetch at 'http://localhost:5000/api/analyze' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solution:**
Backend already has CORS enabled. Make sure you're running the backend AND that `flask-cors` is installed:
```bash
pip install flask-cors
```

### 5. WebSocket connection fails

**Problem:**
```
WebSocket connection to 'ws://localhost:5000/socket.io/' failed
```

**Solution:**
Make sure `flask-socketio` is installed:
```bash
pip install flask-socketio python-socketio eventlet
```

### 6. "Backend Connected" but button still doesn't work

**Check browser console (F12) for errors:**

**If you see:**
```
TypeError: Failed to fetch
```

**Solution:** The frontend can't reach the backend API. Verify:
1. Backend is running: `curl http://localhost:5000/api/health`
2. Frontend proxy is configured in `frontend/package.json`: `"proxy": "http://localhost:5000"`
3. Restart both backend and frontend after config changes

**If you see:**
```
Error 500: Internal Server Error
```

**Solution:** Check backend terminal for Python errors. Common issues:
- Missing dependencies: `pip install -r requirements.txt`
- Config file issues: Check `config.yaml` exists and is valid
- Data files missing: Run a command-line analysis first to populate cache

### 7. Analysis starts but fails immediately

**Check backend terminal for errors:**

**Common errors:**
- `KeyError: 'llm'` → Check `config.yaml` has all required fields
- `ImportError: No module named 'langchain_groq'` → Install: `pip install -r requirements.txt`
- `ValueError: weekend_spec missing race_id` → Query validation failed, try a different query

## Debugging Checklist

Use this checklist to diagnose issues:

- [ ] Backend server is running (`ps aux | grep "python backend/app.py"`)
- [ ] Backend health check passes (`curl http://localhost:5000/api/health`)
- [ ] Frontend is running (`lsof -i :3000`)
- [ ] Browser shows "Backend Connected" in top-right
- [ ] Browser console (F12) shows no errors
- [ ] Virtual environment is activated (`which python` shows f1env_new)
- [ ] All dependencies installed (`pip list | grep flask`)
- [ ] Config file exists (`ls config.yaml`)

## Quick Fix Script

Create a file `fix_web.sh`:
```bash
#!/bin/bash

echo "Fixing F1 Analysis Agent Web Interface..."

# Kill any existing processes
echo "1. Killing existing processes..."
lsof -ti:5000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Install dependencies
echo "2. Installing backend dependencies..."
source f1env_new/bin/activate
pip install -r requirements-web.txt -q

# Check frontend
echo "3. Checking frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "   Installing frontend dependencies..."
    npm install -q
fi
cd ..

# Start backend
echo "4. Starting backend..."
python backend/app.py &
BACKEND_PID=$!

sleep 3

# Check if backend started
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "✅ Backend started successfully!"
    echo "   PID: $BACKEND_PID"
    echo ""
    echo "Now start the frontend:"
    echo "  cd frontend && npm start"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
fi
```

```bash
chmod +x fix_web.sh
./fix_web.sh
```

## Still Not Working?

1. **Check the full logs:**
   - Backend terminal output
   - Browser console (F12 → Console tab)
   - Browser network tab (F12 → Network tab)

2. **Test the backend directly:**
   ```bash
   curl -X POST http://localhost:5000/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"query": "Test query", "depth": "basic"}'
   ```

3. **Restart everything:**
   ```bash
   # Kill all processes
   lsof -ti:5000 | xargs kill -9
   lsof -ti:3000 | xargs kill -9

   # Start fresh
   source f1env_new/bin/activate
   python backend/app.py

   # In another terminal
   cd frontend && npm start
   ```

4. **Check the documentation:**
   - [WEB_INTERFACE_README.md](WEB_INTERFACE_README.md)
   - [QUICK_START.md](QUICK_START.md)

## Contact & Support

If you're still having issues:
1. Check `outputs/analysis_log.txt` for detailed logs
2. Review backend terminal output for Python exceptions
3. Check browser console for JavaScript errors
4. Verify all files were created correctly

---

**Most common fix:** Just start the backend! The frontend needs it to function.
