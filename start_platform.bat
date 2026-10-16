@echo off
powershell -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0start_platform.ps1"
if errorlevel 1 pause
