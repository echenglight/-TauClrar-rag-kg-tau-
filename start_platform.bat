@echo off
set ROOT=%~dp0

echo [1/2] 启动后端 FastAPI...
start powershell -NoExit -Command "Set-Location '%ROOT%backend'; python -m pip install -r requirements.txt; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo [2/2] 启动前端 React...
start powershell -NoExit -Command "Set-Location '%ROOT%frontend'; npm install; npm run dev -- --host"

echo 启动完成。前端: http://localhost:5173  后端: http://localhost:8000
