# AgentBridge 启动脚本
Set-Location "$PSScriptRoot\src\backend"

if (Test-Path "$PSScriptRoot\src\data\oa.db") {
    Write-Host "DB found, starting with existing data"
} else {
    Write-Host "First run, will auto-create seed data"
}

Write-Host "============================================"
Write-Host "  AgentBridge OA - http://127.0.0.1:8001"
Write-Host "  Close this window to stop"
Write-Host "============================================"

python -m uvicorn app.main:app --host 127.0.0.1 --port 8001

pause
