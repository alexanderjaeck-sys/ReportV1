@echo off
cd /d "%~dp0"

:: 1. THE KILL SWITCH: Force close any stuck background Python servers
taskkill /F /IM python.exe >nul 2>&1

:: 2. Start the Streamlit server silently in the background
start /b python -m streamlit run APPSCRIPTV1.py --server.headless=true

:: 3. Wait 8 seconds to ensure the server is fully running
timeout /t 8 /nobreak > NUL

:: 4. Launch the app in a native desktop window
start chrome --app="http://localhost:8501"