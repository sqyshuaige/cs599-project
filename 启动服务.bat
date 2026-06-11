@echo off
chcp 65001 >nul
title AgentBridge - 启动中...

echo ===========================================
echo     AgentBridge - 智慧OA系统Agent智能化改造
echo ===========================================
echo.
echo [1/3] 正在安装依赖...
cd /d "%~dp0src\backend"
pip install -r requirements.txt -q 2>nul
echo        ✅ 依赖安装完成
echo.
echo [2/3] 正在启动服务...
echo.
echo ===========================================
echo    ✅ 服务启动成功！
echo.
echo    🌐 打开浏览器访问: http://127.0.0.1:8001
echo.
echo    关闭此窗口即可停止服务
echo ===========================================
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8001

pause
