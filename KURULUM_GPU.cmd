@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call KURULUM.cmd
".venv\Scripts\python.exe" -m pip install -r requirements-gpu.txt
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -c "from rotary_melter.GpuAnalysis import info; print(info())"
pause
