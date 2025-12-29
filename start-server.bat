@echo off
echo ========================================
echo   Murder Mystery (剧本杀) Server Startup
echo ========================================
echo.

:: Check if .env exists
if not exist "backend\.env" (
    echo [WARNING] backend\.env not found!
    echo Please copy backend\.env.example to backend\.env and add your GOOGLE_API_KEY
    echo.
    pause
    exit /b 1
)

:: Navigate to backend and setup venv if needed
cd /d "%~dp0backend"
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

:: Activate venv and install deps
call venv\Scripts\activate
echo Installing backend dependencies...
pip install -q -r requirements.txt

:: Start backend in background
echo.
echo Starting Backend Server on port 8000...
start /B cmd /c "uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 | findstr /V /C:\"Will watch\""

:: Wait for backend to start
timeout /t 2 /nobreak > nul

:: Navigate to frontend and install deps
cd /d "%~dp0frontend"
echo Installing frontend dependencies...
call npm install --silent

echo.
echo ========================================
echo   Both servers starting!
echo ========================================
echo.
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo   For LAN play, share your IP address:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set ip=%%a
    echo   http://%%a:5173
)
echo.
echo   Press Ctrl+C to stop all servers
echo ========================================
echo.

:: Start frontend in foreground (this keeps the terminal open)
npm run dev -- --host
