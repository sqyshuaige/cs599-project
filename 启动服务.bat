@echo off
cd /d "%~dp0src\backend"
echo Starting AgentBridge OA...
echo http://127.0.0.1:8001
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
pause
