@echo off
REM WhatsApp Clone Launcher for Windows
REM Uganda E-Gov AI Assistant Demo

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    WhatsApp Clone Launcher                   ║
echo ║              Uganda E-Gov AI Assistant Demo                  ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  🤖 AI Backend: http://localhost:8080                       ║
echo ║  💬 WhatsApp Clone: http://localhost:8081                   ║
echo ║  📱 Demo Mode Available (No Google OAuth required)          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "main.py" (
    echo ❌ main.py not found
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

if not exist "whatsapp_clone_server.py" (
    echo ❌ whatsapp_clone_server.py not found
    echo Please ensure all WhatsApp clone files are present
    pause
    exit /b 1
)

echo ✅ Starting WhatsApp Clone Demo...
echo.
echo 💡 This will open two browser windows:
echo    - WhatsApp Clone interface
echo    - API documentation
echo.
echo Press Ctrl+C to stop all services
echo.

REM Run the Python launcher
python launch_whatsapp_clone.py

pause