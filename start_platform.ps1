# 一键启动 TauClear 平台（开发模式）

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[1/2] 启动后端 FastAPI..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\backend'; python -m pip install -r requirements.txt; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Write-Host "[2/2] 启动前端 React..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\frontend'; npm install; npm run dev -- --host"

Write-Host "启动完成。前端：http://localhost:5173  后端：http://localhost:8000"
