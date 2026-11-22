@echo off
cd /d "%~dp0.."
set MINI_HOME=%cd%
call .venv\Scripts\activate
tasklist | find /i "ollama" >nul || start "" /min cmd /c "ollama serve"
start "" http://localhost:3000
cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 3000
