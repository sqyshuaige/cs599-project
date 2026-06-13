@echo off
e:
cd \大作业\smart-oa-agent\src\backend
cls
echo ============================================
echo   AgentBridge OA
echo   http://127.0.0.1:8001
echo ============================================
echo Starting...
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
pause
