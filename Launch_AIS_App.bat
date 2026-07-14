@echo off
cd /d "%~dp0"
echo Running diagnostics...
python -m streamlit run APPSCRIPTV1.py --server.headless=true
pause